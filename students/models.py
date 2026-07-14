from django.core.validators import RegexValidator
from django.db import models

from schools.models import ClassRoom, School


phone_validator = RegexValidator(
    regex=r'^\+?[\d\s\-]{7,15}$',
    message='Enter a valid phone number.',
)


class Gender(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'


class Student(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='students',
    )
    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20)
    admission_number = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
    )
    parent_name = models.CharField(max_length=200, blank=True)
    parent_phone = models.CharField(
        max_length=15,
        validators=[phone_validator],
    )
    address = models.TextField(blank=True)
    face_photo = models.ImageField(upload_to='students/faces/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['roll_number']
        unique_together = [
            ['school', 'roll_number'],
            ['school', 'admission_number'],
        ]
        indexes = [
            models.Index(fields=['school', 'classroom']),
            models.Index(fields=['school', 'is_active']),
        ]

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.roll_number})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()
