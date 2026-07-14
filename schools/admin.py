from django.contrib import admin

from schools.models import ClassRoom, School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'state', 'city']
    search_fields = ['name', 'city', 'phone', 'email']


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'grade', 'section', 'academic_year', 'is_active']
    list_filter = ['is_active', 'academic_year', 'school']
    search_fields = ['name', 'grade', 'section']
