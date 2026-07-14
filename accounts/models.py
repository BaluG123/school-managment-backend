from django.contrib.auth.models import User
from django.db import models


class HeadmasterRole(models.TextChoices):
    HEADMASTER = 'headmaster', 'Headmaster'
    TEACHER = 'teacher', 'Teacher'
    ADMIN = 'admin', 'School Admin'


class HeadmasterProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='headmaster_profile',
    )
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
    )
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(
        max_length=20,
        choices=HeadmasterRole.choices,
        default=HeadmasterRole.HEADMASTER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Headmaster Profile'
        verbose_name_plural = 'Headmaster Profiles'

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'
