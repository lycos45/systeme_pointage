import cv2
import face_recognition
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from .models import Employee, Attendance
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import EmailVerification
from django.urls import reverse
import base64
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.contrib.auth.models import User
from .models import EmailVerification
import face_recognition
import numpy as np
from datetime import date ,timedelta ,datetime,time
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
import secrets
import string
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import json
from django.utils import timezone
from PIL import Image
from .utils.face_recognition_utils import detect_faces, extract_face_descriptor, compare_descriptors
def home(request):
    return render(request, 'home.html')  


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff or user.is_superuser:  # Vérifie si l'utilisateur est un admin
                return redirect('dashboard')  # Redirige vers le tableau de bord
            else:
                return redirect('mark_attendance')  # Redirige vers la page de pointage
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')  
def dashboard(request):
    today = date.today()
    total_employees = Employee.objects.count()
    present_today = Attendance.objects.filter(check_in_time__date=today).count()
    absent_today = total_employees - present_today
    attendance_rate = (present_today / total_employees) * 100 if total_employees > 0 else 0

    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'attendance_rate': attendance_rate,
    }
    return render(request, 'dashboard.html', context)
def verify_email(request, user_id, code):
    try:
        user = User.objects.get(id=user_id)
        verification = EmailVerification.objects.get(user=user, code=code)
        user.is_active = True
        user.save()
        verification.delete()
        return redirect('login')
    except (User.DoesNotExist, EmailVerification.DoesNotExist):
        return render(request, 'invalid_verification.html')





# Vue pour enrôler un employé

def enroll_employee(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        photo_data = request.POST.get('photo')

        # Vérifier si l'email est déjà utilisé
        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Cet email est déjà utilisé."}, status=400)

        # Vérifier si une photo est fournie
        if not photo_data or ';base64,' not in photo_data:
            return JsonResponse({"error": "Photo invalide ou absente."}, status=400)

        try:
            # Convertir l'image base64 en fichier binaire
            format, imgstr = photo_data.split(';base64,')
            ext = format.split('/')[-1]
            photo = ContentFile(base64.b64decode(imgstr), name=f'{name}_profile.{ext}')

            # Lire l'image et extraire les descripteurs faciaux
            image = Image.open(photo)
            face_descriptor = extract_face_descriptor(image)

            if face_descriptor is None:
                return JsonResponse({"error": "Aucun visage détecté."}, status=400)

            # Générer un mot de passe temporaire
            password = generate_password()

            # Créer un utilisateur
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

            # Créer un employé
            employee = Employee.objects.create(
                user=user,
                name=name,
                role=role,
                face_descriptor=face_descriptor.tobytes()  # Convertir en bytes pour le stockage
            )
            employee.profile_picture.save(f'{employee.name}_profile.jpg', photo)

            # Envoi de l'e-mail avec un template HTML
            subject = "Vos informations de connexion"
            html_message = render_to_string('emails/enrollment_email.html', {
                'name': name,
                'email': email,
                'password': password,
                'login_url': "http://votre-site.com/login"
            })

            send_mail(
                subject,
                '',  # On laisse le corps vide car on utilise le format HTML
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
                html_message=html_message
            )

            return JsonResponse({"success": "Enrôlement réussi ! Un e-mail a été envoyé."}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"Une erreur est survenue : {str(e)}"}, status=500)

    return render(request, 'enroll_employee.html')
# Vue pour le pointage des présences


def mark_attendance(request):
    if request.method == "POST":
        try:
            # Lire les données JSON envoyées par le frontend
            data = json.loads(request.body)
            photo_data = data.get('photo')

            if not photo_data:
                return JsonResponse({"error": "Aucune photo n'a été envoyée."}, status=400)

            # Convertir la photo base64 en fichier binaire
            format, imgstr = photo_data.split(';base64,')  # Séparer le préfixe
            ext = format.split('/')[-1]  # Récupérer l'extension (ex: jpeg)
            photo = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')

            # Lire l'image et extraire les descripteurs faciaux
            image = Image.open(photo)
            input_descriptor = extract_face_descriptor(image)

            if input_descriptor is None:
                return JsonResponse({"error": "Aucun visage détecté dans la photo."}, status=400)

            print("Descripteur facial extrait :", input_descriptor)  # Log pour vérifier

            # Comparer avec les employés enregistrés
            employees = Employee.objects.all()
            for employee in employees:
                saved_descriptor = np.frombuffer(employee.face_descriptor, dtype=np.float64)
                print(f"Descripteur stocké pour {employee.name} :", saved_descriptor)  # Log pour vérifier

                match = compare_descriptors(saved_descriptor, input_descriptor, threshold=0.5)

                if match:
                    print(f"Correspondance trouvée pour {employee.name}")  # Log pour vérifier
                    # Déterminer le statut en fonction de l'heure actuelle
                    now = timezone.now()
                    check_in_time = now.time()  # Heure actuelle

                    # Définir les heures limites
                    on_time_limit = time(8, 15)  # 8h15
                    late_limit = time(8, 30)     # 8h30

                    if check_in_time <= on_time_limit:
                        status = 'on_time'
                    elif on_time_limit < check_in_time <= late_limit:
                        status = 'late'
                    else:
                        status = 'absent'

                    # Enregistrer le pointage
                    Attendance.objects.create(employee=employee, check_in_time=now, status=status)
                    return JsonResponse({"success": f"Pointage réussi pour {employee.name} - Statut : {status}"})

            return JsonResponse({"error": "Aucun employé correspondant trouvé."}, status=404)

        except Exception as e:
            return JsonResponse({"error": f"Erreur lors du traitement de l'image : {str(e)}"}, status=500)

    return render(request, 'mark_attendance.html')
# Vue pour la liste des présences
@login_required
def attendance_history(request):
    # Récupérer l'employé connecté (si l'employé est lié à l'utilisateur)
    employee = request.user.employee  # Supposons que l'utilisateur est lié à un employé

    # Récupérer l'historique des pointages pour cet employé
    attendances = Attendance.objects.filter(employee=employee).order_by('-check_in_time')

    context = {
        'attendances': attendances,
    }
    return render(request, 'attendance_history.html', context)
def attendance_list(request):
    # Récupérer toutes les présences
    attendances = Attendance.objects.all().order_by('-check_in_time')

    # Calculer les statistiques
    total_attendances = attendances.count()
    today_attendances = Attendance.objects.filter(check_in_time__date=datetime.today()).count()
    attendance_rate = (today_attendances / Employee.objects.count()) * 100 if Employee.objects.count() > 0 else 0

    context = {
        'attendances': attendances,
        'total_attendances': total_attendances,
        'today_attendances': today_attendances,
        'attendance_rate': round(attendance_rate, 2),
    }

    return render(request, 'attendance_list.html', context)

def generate_password(length=12):
    """Génère un mot de passe aléatoire."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))