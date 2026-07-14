from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from accounts.models import HeadmasterProfile


class HeadmasterProfileInline(admin.StackedInline):
    model = HeadmasterProfile
    can_delete = False
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = [HeadmasterProfileInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
