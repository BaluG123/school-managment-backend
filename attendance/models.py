from django.contrib.auth.models import User
from django.db import models

from schools.models import ClassRoom, School
from students.models import Student


class AttendanceStatus(models.TextChoices):
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'
    LATE = 'late', 'Late'
    HALF_DAY = 'half_day', 'Half Day'


class Attendance(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_records',
    )
    date = models.DateField()
    check_in_time = models.DateTimeField()
    status = models.CharField(
        max_length=10,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_marked',
    )
    face_match_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text='Face match confidence score (0-100) from mobile app.',
    )
    capture_photo = models.ImageField(
        upload_to='attendance/captures/',
        blank=True,
        null=True,
        help_text='Photo captured during attendance marking.',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-check_in_time']
        unique_together = [['student', 'date']]
        indexes = [
            models.Index(fields=['school', 'date']),
            models.Index(fields=['classroom', 'date']),
            models.Index(fields=['student', 'date']),
        ]
        verbose_name_plural = 'Attendance records'

    def __str__(self):
        return f'{self.student} - {self.date} ({self.status})'
