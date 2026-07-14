from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from attendance.models import Attendance, AttendanceStatus
from attendance.serializers import (
    AttendanceSerializer,
    BulkMarkAttendanceSerializer,
    ClassAttendanceSummarySerializer,
    MarkAttendanceSerializer,
    StudentAttendanceSummarySerializer,
)
from core.permissions import IsSchoolStaff
from schools.models import ClassRoom
from students.models import Student


class MarkAttendanceView(generics.CreateAPIView):
    """
    Mark attendance for a single student.
    Called by the React Native app after face recognition + liveness check.
    """

    permission_classes = [IsSchoolStaff]
    serializer_class = MarkAttendanceSerializer
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=['Attendance'],
        summary='Mark attendance for a student (face recognition)',
        description=(
            'Mark daily attendance after the mobile app matches the student face. '
            'If attendance already exists for today, it will be updated.'
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attendance = serializer.save()

        message = (
            'Attendance marked successfully.'
            if getattr(attendance, '_was_created', True)
            else 'Attendance updated for today.'
        )

        return Response(
            {
                'message': message,
                'attendance': AttendanceSerializer(
                    attendance,
                    context={'request': request},
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class BulkMarkAttendanceView(APIView):
    """Manual bulk attendance marking (fallback when face recognition is unavailable)."""

    permission_classes = [IsSchoolStaff]

    @extend_schema(
        tags=['Attendance'],
        summary='Bulk mark attendance manually',
    )
    def post(self, request):
        serializer = BulkMarkAttendanceSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        target_date = serializer.validated_data.get('date') or timezone.localdate()
        records = serializer.validated_data['records']
        created_count = 0
        updated_count = 0
        results = []

        for record in records:
            student = Student.objects.select_related('school', 'classroom').get(
                pk=record['student_id'],
            )
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=target_date,
                defaults={
                    'school': student.school,
                    'classroom': student.classroom,
                    'check_in_time': timezone.now(),
                    'status': record.get('status', AttendanceStatus.PRESENT),
                    'marked_by': request.user,
                    'notes': record.get('notes', ''),
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
            results.append(AttendanceSerializer(attendance).data)

        return Response({
            'message': f'Processed {len(records)} records.',
            'created': created_count,
            'updated': updated_count,
            'attendance': results,
        })


class AttendanceListView(generics.ListAPIView):
    permission_classes = [IsSchoolStaff]
    serializer_class = AttendanceSerializer

    @extend_schema(
        tags=['Attendance'],
        summary='List attendance records with filters',
        parameters=[
            OpenApiParameter('date', str, description='Filter by date (YYYY-MM-DD)'),
            OpenApiParameter('classroom', int, description='Filter by classroom ID'),
            OpenApiParameter('student', int, description='Filter by student ID'),
            OpenApiParameter('status', str, description='Filter by status'),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        profile = self.request.user.headmaster_profile
        qs = Attendance.objects.filter(
            school_id=profile.school_id,
        ).select_related('student', 'classroom', 'school')

        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(date=date)

        classroom_id = self.request.query_params.get('classroom')
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)

        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(student_id=student_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        return qs


class ClassAttendanceReportView(APIView):
    """Class-wise attendance report for a specific date."""

    permission_classes = [IsSchoolStaff]

    @extend_schema(
        tags=['Attendance'],
        summary='Class-wise attendance report',
        parameters=[
            OpenApiParameter('classroom', int, required=True),
            OpenApiParameter('date', str, description='Date (YYYY-MM-DD), defaults to today'),
        ],
    )
    def get(self, request):
        classroom_id = request.query_params.get('classroom')
        if not classroom_id:
            return Response(
                {'classroom': 'classroom query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = request.user.headmaster_profile
        target_date = request.query_params.get('date') or timezone.localdate()

        try:
            classroom = ClassRoom.objects.get(
                pk=classroom_id,
                school_id=profile.school_id,
            )
        except ClassRoom.DoesNotExist:
            return Response(
                {'detail': 'Classroom not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        total_students = Student.objects.filter(
            classroom=classroom,
            is_active=True,
        ).count()

        status_counts = Attendance.objects.filter(
            classroom=classroom,
            date=target_date,
        ).values('status').annotate(count=Count('id'))

        counts = {s['status']: s['count'] for s in status_counts}
        present = counts.get(AttendanceStatus.PRESENT, 0)
        absent = counts.get(AttendanceStatus.ABSENT, 0)
        late = counts.get(AttendanceStatus.LATE, 0)
        half_day = counts.get(AttendanceStatus.HALF_DAY, 0)
        marked_total = present + absent + late + half_day
        unmarked = max(total_students - marked_total, 0)

        attendance_records = Attendance.objects.filter(
            classroom=classroom,
            date=target_date,
        ).select_related('student')

        students = Student.objects.filter(
            classroom=classroom,
            is_active=True,
        ).order_by('roll_number')

        marked_student_ids = set(
            attendance_records.values_list('student_id', flat=True)
        )

        student_details = []
        for student in students:
            record = attendance_records.filter(student=student).first()
            student_details.append({
                'student_id': student.id,
                'full_name': student.full_name,
                'roll_number': student.roll_number,
                'status': record.status if record else 'unmarked',
                'check_in_time': record.check_in_time if record else None,
                'face_match_confidence': record.face_match_confidence if record else None,
            })

        percentage = (
            round((present + late) / total_students * 100, 2)
            if total_students > 0 else 0
        )

        summary = {
            'classroom_id': classroom.id,
            'classroom_name': classroom.name,
            'date': target_date,
            'total_students': total_students,
            'present': present,
            'absent': absent,
            'late': late,
            'half_day': half_day,
            'unmarked': unmarked,
            'attendance_percentage': percentage,
            'students': student_details,
        }

        return Response(summary)


class StudentAttendanceReportView(APIView):
    """Student-wise attendance history and summary."""

    permission_classes = [IsSchoolStaff]

    @extend_schema(
        tags=['Attendance'],
        summary='Student-wise attendance report',
        parameters=[
            OpenApiParameter('student', int, required=True),
            OpenApiParameter('from', str, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter('to', str, description='End date (YYYY-MM-DD)'),
        ],
    )
    def get(self, request):
        student_id = request.query_params.get('student')
        if not student_id:
            return Response(
                {'student': 'student query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = request.user.headmaster_profile

        try:
            student = Student.objects.get(
                pk=student_id,
                school_id=profile.school_id,
            )
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        qs = Attendance.objects.filter(student=student)

        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        total_days = qs.count()
        present_days = qs.filter(
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE],
        ).count()
        absent_days = qs.filter(status=AttendanceStatus.ABSENT).count()
        late_days = qs.filter(status=AttendanceStatus.LATE).count()

        percentage = (
            round(present_days / total_days * 100, 2)
            if total_days > 0 else 0
        )

        records = AttendanceSerializer(
            qs.order_by('-date'),
            many=True,
            context={'request': request},
        ).data

        return Response({
            'student_id': student.id,
            'student_name': student.full_name,
            'roll_number': student.roll_number,
            'classroom': student.classroom.name if student.classroom else None,
            'summary': {
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'attendance_percentage': percentage,
            },
            'records': records,
        })


class DailyAttendanceDashboardView(APIView):
    """School-wide daily attendance overview across all classrooms."""

    permission_classes = [IsSchoolStaff]

    @extend_schema(
        tags=['Attendance'],
        summary='Daily attendance dashboard for entire school',
        parameters=[
            OpenApiParameter('date', str, description='Date (YYYY-MM-DD), defaults to today'),
        ],
    )
    def get(self, request):
        profile = request.user.headmaster_profile
        target_date = request.query_params.get('date') or timezone.localdate()

        classrooms = ClassRoom.objects.filter(
            school_id=profile.school_id,
            is_active=True,
        )

        class_summaries = []
        total_students = 0
        total_present = 0

        for classroom in classrooms:
            students_count = Student.objects.filter(
                classroom=classroom,
                is_active=True,
            ).count()

            present_count = Attendance.objects.filter(
                classroom=classroom,
                date=target_date,
                status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE],
            ).count()

            total_students += students_count
            total_present += present_count

            class_summaries.append({
                'classroom_id': classroom.id,
                'classroom_name': classroom.name,
                'total_students': students_count,
                'present': present_count,
                'attendance_percentage': (
                    round(present_count / students_count * 100, 2)
                    if students_count > 0 else 0
                ),
            })

        return Response({
            'date': target_date,
            'school_id': profile.school_id,
            'total_students': total_students,
            'total_present': total_present,
            'overall_percentage': (
                round(total_present / total_students * 100, 2)
                if total_students > 0 else 0
            ),
            'classrooms': class_summaries,
        })
