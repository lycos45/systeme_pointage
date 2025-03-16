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
from django.http import JsonResponse,HttpResponseNotAllowed,HttpResponse
from django.core.files.base import ContentFile
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
import torch 
from attendance.utils.face_recognition_utils import detect_faces, extract_face_descriptor, compare_descriptors
from .forms import ProfileUpdateForm, PasswordUpdateForm
from django.contrib.auth import update_session_auth_hash
from collections import defaultdict

from .forms import WorkScheduleForm, GlobalWorkScheduleForm
from .models import WorkSchedule, GlobalWorkSchedule, Employee

def home(request):
    return render(request, 'home.html')  

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Logique pour envoyer l'e-mail (à implémenter)
            pass
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})
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
@login_required
def dashboard(request):
    # Récupérer les paramètres de filtre (par défaut : aujourd'hui)
    filter_type = request.GET.get('filter', 'today')  # today, week, month, custom
    employee_id = request.GET.get('employee')  # Filtrer par employé

    # Définir la période en fonction du filtre
    today = date.today()
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'week':
        start_date = today - timedelta(days=today.weekday())  # Début de la semaine (lundi)
        end_date = start_date + timedelta(days=6)
    elif filter_type == 'month':
        start_date = today.replace(day=1)  # Début du mois
        end_date = start_date.replace(day=28) + timedelta(days=4)  # Fin du mois
    else:
        # Filtre personnalisé (à implémenter)
        start_date = today
        end_date = today

    # Récupérer les données filtrées
    attendances = Attendance.objects.filter(
        check_in_time__date__range=[start_date, end_date],
        status__in=['on_time', 'late']
    )

    if employee_id:
        attendances = attendances.filter(employee_id=employee_id)

    # Calculer les statistiques
    total_employees = Employee.objects.count()
    present_count = attendances.distinct('employee').count()
    absent_count = total_employees - present_count
    attendance_rate = (present_count / total_employees) * 100 if total_employees > 0 else 0

    # Récupérer la liste des employés pour le filtre
    employees = Employee.objects.all()

    context = {
        'total_employees': total_employees,
        'present_today': present_count,
        'absent_today': absent_count,
        'attendance_rate': round(attendance_rate, 2),
        'employees': employees,
        'filter_type': filter_type,
        'selected_employee_id': int(employee_id) if employee_id else None,
    }

    return render(request, 'dashboard.html', context)
@login_required
def employee_details(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    attendances = Attendance.objects.filter(employee=employee).order_by('-check_in_time')

    context = {
        'employee': employee,
        'attendances': attendances,
    }

    return render(request, 'employee_details.html', context)
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
# Créer une instance de MTCNN pour la détection des visages
@login_required
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

            # Charger l'image avec PIL
            image = Image.open(photo).convert('RGB')  # S'assurer qu'elle est en RGB

            # Extraire le descripteur facial
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

            # Créer un employé avec le descripteur sous forme de bytes
            employee = Employee.objects.create(
                user=user,
                name=name,
                role=role,
                face_descriptor=face_descriptor.tobytes()
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
                '',  # Corps vide car on utilise un template HTML
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
@login_required
def mark_attendance(request):
    if request.method == "POST":
        try:
            # Lire les données JSON envoyées par le frontend
            data = json.loads(request.body)
            photo_data = data.get('photo')

            if not photo_data:
                return JsonResponse({"error": "Aucune photo n'a été envoyée."}, status=400)

            # Convertir la photo base64 en fichier binaire
            try:
                photo = ContentFile(base64.b64decode(photo_data), name='temp.jpg')
            except Exception as e:
                return JsonResponse({"error": "Format de photo invalide."}, status=400)

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

                    # Récupérer la date du jour
                    today = timezone.now().date()

                    # Vérifier si l'employé a déjà pointé aujourd'hui
                    existing_attendance = Attendance.objects.filter(
                        employee=employee,
                        check_in_time__date=today
                    ).first()

                    # Déterminer le statut en utilisant la fonction
                    status = determine_attendance_status(employee)

                    if existing_attendance:
                        # Mettre à jour le pointage existant
                        existing_attendance.check_in_time = timezone.now()
                        existing_attendance.status = status
                        existing_attendance.save()
                        message = f"Pointage mis à jour pour {employee.name} - Statut : {status}"
                    else:
                        # Créer un nouveau pointage
                        Attendance.objects.create(
                            employee=employee,
                            check_in_time=timezone.now(),
                            status=status
                        )
                        message = f"Pointage réussi pour {employee.name} - Statut : {status}"

                    return JsonResponse({"success": message})

            return JsonResponse({"error": "Aucun employé correspondant trouvé."}, status=404)

        except Exception as e:
            return JsonResponse({"error": f"Erreur lors du traitement de l'image : {str(e)}"}, status=500)

    elif request.method == "GET":
        # Afficher la page de pointage pour les requêtes GET
        return render(request, 'mark_attendance.html')

    # Retourner une réponse pour les autres méthodes (PUT, DELETE, etc.)
    return HttpResponseNotAllowed(['GET', 'POST'])
# Vue pour la liste des présences
@login_required
def attendance_history(request):
    # Récupérer l'employé connecté
    employee = request.user.employee

    # Récupérer l'historique des pointages et trier par date décroissante
    attendances = Attendance.objects.filter(employee=employee).order_by('-check_in_time')

    # Debug : Afficher les données récupérées
    print("Employee:", employee)
    print("Attendances QuerySet:", attendances)
    print("Attendances Count:", attendances.count())

    # Grouper les pointages par date
    grouped_attendances = defaultdict(list)
    for attendance in attendances:
        date_key = attendance.check_in_time.date()  # Extrait uniquement la date (sans l'heure)
        grouped_attendances[date_key].append(attendance)

    # Debug : Afficher les données groupées
    print("Grouped Attendances:", grouped_attendances)

    context = {
        'grouped_attendances': dict(grouped_attendances),
    }
    return render(request, 'attendance_history.html', context)
@login_required
def attendance_list(request):
    today = timezone.now().date()

    # Récupérer la dernière présence de chaque employé pour aujourd'hui
    attendances = Attendance.objects.filter(
        check_in_time__date=today
    ).order_by('employee', '-check_in_time').distinct('employee')

    # Filtrer pour exclure les statuts "absent"
    attendances = [attendance for attendance in attendances if attendance.status != 'absent']

    # Calculer les statistiques
    total_attendances = len(attendances)
    today_attendances = total_attendances
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

@login_required
def settings_view(request):
    # Récupérer l'employé connecté
    employee = Employee.objects.get(user=request.user)

    if request.method == 'POST':
        # Formulaire de mise à jour du profil
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=employee)
        # Formulaire de mise à jour du mot de passe
        password_form = PasswordUpdateForm(request.user, request.POST)

        if 'update_profile' in request.POST:
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Votre profil a été mis à jour avec succès.')
                return redirect('settings')

        elif 'update_password' in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Mettre à jour la session pour éviter la déconnexion
                messages.success(request, 'Votre mot de passe a été mis à jour avec succès.')
                return redirect('settings')

    else:
        profile_form = ProfileUpdateForm(instance=employee)
        password_form = PasswordUpdateForm(request.user)

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }

    return render(request, 'settings.html', context)

@login_required
def determine_attendance_status(employee):
    """
    Détermine le statut de pointage (à l'heure, en retard, absent) pour un employé.
    :param employee: L'employé à vérifier.
    :return: Statut de pointage ('on_time', 'late', 'absent').
    """
    # Obtenir l'heure actuelle avec fuseau horaire
    now = timezone.now()
    today = now.date()

    # Récupérer l'horaire de travail de l'employé pour aujourd'hui
    schedule = WorkSchedule.objects.filter(
        employee=employee,
        day_of_week=today.strftime('%A')  # Exemple : "Monday"
    ).first()

    if not schedule:
        return 'absent'  # Pas d'horaire défini pour aujourd'hui

    # Convertir l'heure de début en datetime "aware" pour comparaison
    start_time = timezone.make_aware(datetime.combine(today, schedule.start_time))

    # Déterminer le statut
    if now <= start_time:
        return 'on_time'
    else:
        return 'late'

@login_required
def manage_work_schedules(request):
    if request.method == 'POST':
        if 'global_schedule' in request.POST:
            global_form = GlobalWorkScheduleForm(request.POST)
            if global_form.is_valid():
                global_form.save()
                return redirect('manage_work_schedules')
        else:
            form = WorkScheduleForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('manage_work_schedules')
    else:
        form = WorkScheduleForm()
        global_form = GlobalWorkScheduleForm()

    # Récupérer tous les horaires de travail
    work_schedules = WorkSchedule.objects.all()
    global_schedules = GlobalWorkSchedule.objects.all()

    context = {
        'form': form,
        'global_form': global_form,
        'work_schedules': work_schedules,
        'global_schedules': global_schedules,
    }
    return render(request, 'manage_work_schedules.html', context)
def calendrier_view(request):
    work_schedules = WorkSchedule.objects.select_related('employee').all()
    print(work_schedules)  # Vérifie si les horaires sont bien récupérés
    return render(request, 'manage_work_schedules.html', {'work_schedules': work_schedules})
