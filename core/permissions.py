from rest_framework.permissions import BasePermission


class IsSchoolStaff(BasePermission):
    """Allow access only to authenticated users linked to a school."""

    message = 'You must be linked to a school to perform this action.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, 'headmaster_profile', None)
        return profile is not None and profile.school_id is not None


class IsSchoolOwnerOrStaff(BasePermission):
    """Allow school creator or any staff member of that school."""

    def has_object_permission(self, request, view, obj):
        profile = getattr(request.user, 'headmaster_profile', None)
        if not profile or not profile.school_id:
            return False

        school_id = getattr(obj, 'school_id', None) or getattr(obj, 'id', None)
        if hasattr(obj, 'school'):
            school_id = obj.school_id

        return profile.school_id == school_id
