from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models


phone_validator = RegexValidator(
    regex=r'^\+?[\d\s\-]{7,15}$',
    message='Enter a valid phone number.',
)


class School(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(
        max_length=10,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{6}$',
                message='Pincode must be a 6-digit number.',
            )
        ],
    )
    phone = models.CharField(max_length=15, validators=[phone_validator])
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='schools/logos/', blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='schools_created',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class ClassRoom(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classrooms',
    )
    name = models.CharField(max_length=50, help_text='e.g. Class 10-A')
    grade = models.CharField(max_length=20, help_text='e.g. 10')
    section = models.CharField(max_length=10, blank=True, help_text='e.g. A')
    academic_year = models.CharField(
        max_length=20,
        help_text='e.g. 2025-2026',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['grade', 'section']
        unique_together = [['school', 'grade', 'section', 'academic_year']]
        verbose_name = 'Classroom'
        verbose_name_plural = 'Classrooms'

    def __str__(self):
        return f'{self.name} ({self.school.name})'
