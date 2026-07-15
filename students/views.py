from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsSchoolStaff
from students.models import Student
from students.serializers import (
    StudentFacePhotoSerializer,
    StudentListSerializer,
    StudentSerializer,
)


@extend_schema_view(
    get=extend_schema(tags=['Students'], summary='List students'),
    post=extend_schema(tags=['Students'], summary='Register a new student'),
)
class StudentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsSchoolStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StudentListSerializer
        return StudentSerializer

    def get_queryset(self):
        profile = self.request.user.headmaster_profile
        qs = Student.objects.filter(school_id=profile.school_id)

        classroom_id = self.request.query_params.get('classroom')
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                first_name__icontains=search,
            ) | qs.filter(
                last_name__icontains=search,
            ) | qs.filter(
                roll_number__icontains=search,
            )

        return qs.select_related('classroom', 'school')

    def perform_create(self, serializer):
        profile = self.request.user.headmaster_profile
        serializer.save(school_id=profile.school_id, is_active=True)


@extend_schema_view(
    get=extend_schema(tags=['Students'], summary='Get student details'),
    put=extend_schema(tags=['Students'], summary='Update student'),
    patch=extend_schema(tags=['Students'], summary='Partially update student'),
    delete=extend_schema(tags=['Students'], summary='Deactivate student'),
)
class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSchoolStaff]
    serializer_class = StudentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        profile = self.request.user.headmaster_profile
        return Student.objects.filter(
            school_id=profile.school_id,
        ).select_related('classroom', 'school')

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])


class StudentFacePhotoUpdateView(generics.UpdateAPIView):
    """Update only the face photo — useful when re-enrolling a student."""

    permission_classes = [IsSchoolStaff]
    serializer_class = StudentFacePhotoSerializer
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['patch', 'put']

    def get_queryset(self):
        profile = self.request.user.headmaster_profile
        return Student.objects.filter(school_id=profile.school_id)

    @extend_schema(tags=['Students'], summary='Update student face photo')
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class StudentFacePhotosListView(APIView):
    """
    Returns all active students with face photos for a classroom.
    Used by the mobile app to download reference photos for face matching.
    """

    permission_classes = [IsSchoolStaff]

    @extend_schema(
        tags=['Students'],
        summary='Get face photos for a classroom (for mobile face matching)',
    )
    def get(self, request):
        classroom_id = request.query_params.get('classroom')
        if not classroom_id:
            return Response(
                {'classroom': 'classroom query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = request.user.headmaster_profile
        students = Student.objects.filter(
            school_id=profile.school_id,
            classroom_id=classroom_id,
            is_active=True,
        ).only('id', 'first_name', 'last_name', 'roll_number', 'face_photo')

        data = [
            {
                'id': s.id,
                'full_name': s.full_name,
                'roll_number': s.roll_number,
                'face_photo': (
                    request.build_absolute_uri(s.face_photo.url)
                    if s.face_photo
                    else None
                ),
                'has_face_photo': bool(s.face_photo),
            }
            for s in students
        ]
        return Response({
            'classroom': classroom_id,
            'count': len(data),
            'with_photos': sum(1 for d in data if d['has_face_photo']),
            'students': data,
        })
