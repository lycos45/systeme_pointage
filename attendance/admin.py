# Register your models here.
from django.contrib import admin
#from .models import TestModel
from .models import Employee, WorkSchedule, Attendance

#admin.site.register(TestModel)
admin.site.register(Employee)
admin.site.register(WorkSchedule)
admin.site.register(Attendance)