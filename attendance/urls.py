from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home, name='home'),  # Route pour la racine, redirige vers la vue home
    path('enroll/', views.enroll_employee, name='enroll_employee'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('list/', views.attendance_list, name='attendance_list'),
    path('login/', views.login_view, name='login'),  # Connexion
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('attendance-history/', views.attendance_history, name='attendance_history'),
    path('settings/', views.settings_view, name='settings'),
    path('employee/<int:employee_id>/', views.employee_details, name='employee_details'),
    path('manage/work-schedules/', views.manage_work_schedules, name='manage_work_schedules'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)