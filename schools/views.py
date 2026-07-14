from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import HeadmasterProfile
from core.permissions import IsSchoolStaff
from schools.models import ClassRoom, School
from schools.serializers import ClassRoomSerializer, SchoolCreateSerializer, SchoolSerializer


@extend_schema_view(
    get=extend_schema(tags=['Schools'], summary='List schools for current user'),
    post=extend_schema(tags=['Schools'], summary='Create a new school'),
)
class SchoolListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SchoolCreateSerializer
        return SchoolSerializer

    def get_queryset(self):
        profile = self.request.user.headmaster_profile
        return School.objects.filter(
            staff__user=self.request.user,
        ).annotate(
            classroom_count=Count('classrooms', distinct=True),
            student_count=Count('students', distinct=True),
        )

    def perform_create(self, serializer):
        school = serializer.save(created_by=self.request.user)
        profile = self.request.user.headmaster_profile
        profile.school = school
        profile.save(update_fields=['school', 'updated_at'])


@extend_schema_view(
    get=extend_schema(tags=['Schools'], summary='Get school details'),
    put=extend_schema(tags=['Schools'], summary='Update school'),
    patch=extend_schema(tags=['Schools'], summary='Partially update school'),
)
class SchoolDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsSchoolStaff]
    serializer_class = SchoolSerializer

    def get_queryset(self):
        profile = self.request.user.headmaster_profile
        return School.objects.filter(id=profile.school_id).annotate(
            classroom_count=Count('classrooms', distinct=True),
            student_count=Count('students', distinct=True),
        )


@extend_schema_view(
    get=extend_schema(tags=['Classrooms'], summary='List classrooms'),
    post=extend_schema(tags=['Classrooms'], summary='Create a classroom'),
)
class ClassRoomListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSchoolStaff]
    serializer_class = ClassRoomSerializer

    def get_queryset(self):
        profile = self.request.user.headmaster_profile
        return ClassRoom.objects.filter(
            school_id=profile.school_id,
        ).annotate(
            student_count=Count('students', distinct=True),
        )

    def perform_create(self, serializer):
        profile = self.request.user.headmaster_profile
        serializer.save(school_id=profile.school_id)


@extend_schema_view(
    get=extend_schema(tags=['Classrooms'], summary='Get classroom details'),
    put=extend_schema(tags=['Classrooms'], summary='Update classroom'),
    patch=extend_schema(tags=['Classrooms'], summary='Partially update classroom'),
    delete=extend_schema(tags=['Classrooms'], summary='Deactivate classroom'),
)
class ClassRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSchoolStaff]
    serializer_class = ClassRoomSerializer

    def get_queryset(self):
        profile = self.request.user.headmaster_profile
        return ClassRoom.objects.filter(
            school_id=profile.school_id,
        ).annotate(
            student_count=Count('students', distinct=True),
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
