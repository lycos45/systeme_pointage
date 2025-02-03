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
from datetime import date ,timedelta ,datetime
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt


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


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']

        # Vérifier que les mots de passe correspondent
        if password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('register')

        try:
            # Créer un nouvel utilisateur
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            user.save()

            # Créer un employé et le lier à l'utilisateur
            employee = Employee.objects.create(
                user=user,  # Lie l'employé à l'utilisateur
                name=f"{first_name} {last_name}",  # Utilise le nom complet
                email=email,
                role='employee',  # Par défaut, le rôle est 'employee'
            )
            employee.save()

            messages.success(request, "Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.")
            return redirect('login')  # Redirige vers la page de connexion après l'inscription réussie
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
            return redirect('register')
    return render(request, 'register.html')


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



def send_verification_email(user):
    code = get_random_string(length=6, allowed_chars='0123456789')
    EmailVerification.objects.create(user=user, code=code)
    verification_url = f'http://votre_site.com/verify_email/{user.id}/{code}/'
    send_mail(
    'Test Email',
    'Ceci est un test d\'envoi d\'e-mail.',
    'your_email@gmail.com',
    ['destination_email@example.com'],
    fail_silently=False,
)

# Vue pour enrôler un employé

def enroll_employee(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        photo_data = request.POST.get('photo')  # Récupérer les données base64

        # Vérifier si l'email est déjà utilisé
        if Employee.objects.filter(email=email).exists():
            return JsonResponse({"error": "Cet email est déjà utilisé."}, status=400)

        # Convertir l'image base64 en fichier binaire
        if photo_data:
            format, imgstr = photo_data.split(';base64,')  # Séparer le préfixe
            ext = format.split('/')[-1]  # Récupérer l'extension (ex: jpeg)
            photo = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        else:
            return JsonResponse({"error": "Aucune photo n'a été capturée."}, status=400)

        # Lire l'image et extraire les descripteurs faciaux
        image = face_recognition.load_image_file(photo)
        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) == 0:
            return JsonResponse({"error": "Aucun visage détecté dans la photo."}, status=400)

        face_descriptor = face_encodings[0]  # Utilise le premier visage détecté

        # Enregistrer l'employé dans la base de données
        employee = Employee.objects.create(
            name=name,
            email=email,
            role=role,
            face_descriptor=face_descriptor.tobytes()  # Sauvegarde des descripteurs
        )
        employee.profile_picture.save(f'{employee.name}_profile.jpg', photo)

        return JsonResponse({"success": "Enrôlement réussi !"}, status=200)

    return render(request, 'enroll_employee.html')
# Vue pour le pointage des présences

def mark_attendance(request):
    if request.method == "POST":
        try:
            # Récupérer la photo en base64
            data = request.POST.get('photo')
            if not data:
                return JsonResponse({"error": "Aucune photo n'a été envoyée."}, status=400)

            # Convertir la photo base64 en fichier binaire
            format, imgstr = data.split(';base64,')  # Séparer le préfixe
            ext = format.split('/')[-1]  # Récupérer l'extension (ex: jpeg)
            photo = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')

            # Lire l'image et extraire les descripteurs faciaux
            image = face_recognition.load_image_file(photo)
            face_encodings = face_recognition.face_encodings(image)

            if len(face_encodings) == 0:
                return JsonResponse({"error": "Aucun visage détecté dans la photo."}, status=400)

            input_descriptor = face_encodings[0]

            # Comparer avec les employés enregistrés
            employees = Employee.objects.all()
            for employee in employees:
                saved_descriptor = np.frombuffer(employee.face_descriptor, dtype=np.float64)
                match = face_recognition.compare_faces([saved_descriptor], input_descriptor)

                if match[0]:
                    # Enregistrer le pointage
                    Attendance.objects.create(employee=employee, status='on_time')
                    return JsonResponse({"success": f"Pointage réussi pour {employee.name}"})

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