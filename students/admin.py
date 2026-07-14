from django.contrib import admin

from students.models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'roll_number', 'school', 'classroom',
        'is_active', 'created_at',
    ]
    list_filter = ['is_active', 'school', 'classroom', 'gender']
    search_fields = [
        'first_name', 'last_name', 'roll_number',
        'admission_number', 'parent_phone',
    ]
