from django.db import models
from django.contrib.auth.models import User
import numpy as np
from django.utils import timezone
from django import forms


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)  # Lien vers l'utilisateur
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=[('admin', 'Admin'), ('employee', 'Employee')])
    created_at = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    face_descriptor = models.BinaryField(blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def email(self):
        return self.user.email  # Utilisez l'e-mail de l'utilisateur lié

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
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField(default=timezone.now)  # Heure de pointage
    status = models.CharField(
        max_length=20,
        choices=[('on_time', 'À l\'heure'), ('late', 'En retard'), ('absent', 'Absent')],
        default='on_time'
    )

    def __str__(self):
        return f"{self.employee.name} - {self.check_in_time} - {self.status}"

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

