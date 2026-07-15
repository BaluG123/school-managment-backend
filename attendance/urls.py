from django.urls import path

from attendance.views import (
    AttendanceListView,
    BulkMarkAttendanceView,
    ClassAttendanceReportView,
    DailyAttendanceDashboardView,
    MarkAttendanceView,
    MatchAndMarkAttendanceView,
    StudentAttendanceReportView,
)

urlpatterns = [
    path('mark/', MarkAttendanceView.as_view(), name='attendance-mark'),
    path('match/', MatchAndMarkAttendanceView.as_view(), name='attendance-match'),
    path('bulk-mark/', BulkMarkAttendanceView.as_view(), name='attendance-bulk-mark'),
    path('', AttendanceListView.as_view(), name='attendance-list'),
    path('class-report/', ClassAttendanceReportView.as_view(), name='attendance-class-report'),
    path('student-report/', StudentAttendanceReportView.as_view(), name='attendance-student-report'),
    path('dashboard/', DailyAttendanceDashboardView.as_view(), name='attendance-dashboard'),
]
