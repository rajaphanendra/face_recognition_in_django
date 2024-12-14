from django.contrib import admin
from .models import User, Attendance

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('uid', 'name', 'image_path')
    search_fields = ('uid', 'name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('uid', 'name', 'in_time', 'out_time', 'date')
    search_fields = ('uid', 'name', 'date')
    list_filter = ('date', 'uid')
