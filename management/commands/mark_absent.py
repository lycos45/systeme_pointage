from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, time
from yourapp.models import Employee, Attendance

class Command(BaseCommand):
    help = 'Marque les employés absents après 8h30.'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        today = now.date()

        # Heure limite pour être marqué absent
        absent_limit = time(8, 30)

        # Récupérer tous les employés
        employees = Employee.objects.all()

        for employee in employees:
            # Vérifier si l'employé a déjà pointé aujourd'hui
            has_attendance = Attendance.objects.filter(
                employee=employee,
                check_in_time__date=today
            ).exists()

            if not has_attendance and now.time() > absent_limit:
                # Marquer l'employé comme absent
                Attendance.objects.create(
                    employee=employee,
                    check_in_time=now,
                    status='absent'
                )
                self.stdout.write(f"{employee.name} marqué comme absent.")