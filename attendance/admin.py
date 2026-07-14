from django.contrib import admin

from attendance.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'date', 'status', 'check_in_time',
        'face_match_confidence', 'marked_by',
    ]
    list_filter = ['status', 'date', 'school', 'classroom']
    search_fields = [
        'student__first_name', 'student__last_name',
        'student__roll_number',
    ]
    date_hierarchy = 'date'
