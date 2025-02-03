from django.db import models
from django.contrib.auth.models import User
import numpy as np

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)  # Lien vers l'utilisateur
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=[('admin', 'Admin'), ('employee', 'Employee')])
    created_at = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    face_descriptor = models.BinaryField(blank=True, null=True)

    def __str__(self):
        return self.name

class WorkSchedule(models.Model):
    """Horaires de travail des employés."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    day_of_week = models.CharField(max_length=10, choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ])

    def __str__(self):
        return f"{self.employee.name} - {self.day_of_week}"


class Attendance(models.Model):
    """Enregistrements des présences."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('on_time', 'On Time'),
        ('late', 'Late'),
        ('absent', 'Absent'),
    ])

    def __str__(self):
        return f"{self.employee.name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M:%S')}"


class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
