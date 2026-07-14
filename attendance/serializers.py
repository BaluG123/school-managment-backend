from django.utils import timezone
from rest_framework import serializers

from attendance.models import Attendance, AttendanceStatus
from core.validators import validate_image_file
from students.models import Student


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    classroom_name = serializers.CharField(
        source='classroom.name',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'roll_number',
            'school', 'classroom', 'classroom_name',
            'date', 'check_in_time', 'status',
            'face_match_confidence', 'capture_photo', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'school', 'classroom', 'created_at', 'updated_at']

    def validate_capture_photo(self, value):
        if value:
            validate_image_file(value)
        return value

    def validate_face_match_confidence(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError(
                'Confidence must be between 0 and 100.'
            )
        return value

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                'Attendance date cannot be in the future.'
            )
        return value


class MarkAttendanceSerializer(serializers.Serializer):
    """Used by the mobile app to mark attendance after face recognition."""

    student_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )
    face_match_confidence = serializers.FloatField(
        required=False,
        allow_null=True,
        min_value=0,
        max_value=100,
    )
    capture_photo = serializers.ImageField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)
    check_in_time = serializers.DateTimeField(required=False)

    def validate_capture_photo(self, value):
        if value:
            validate_image_file(value)
        return value

    def validate_student_id(self, value):
        request = self.context['request']
        profile = request.user.headmaster_profile

        try:
            student = Student.objects.select_related('school', 'classroom').get(
                pk=value,
                school_id=profile.school_id,
                is_active=True,
            )
        except Student.DoesNotExist:
            raise serializers.ValidationError(
                'Student not found or does not belong to your school.'
            )

        self.context['student'] = student
        return value

    def create(self, validated_data):
        student = self.context['student']
        request = self.context['request']
        today = timezone.localdate()
        check_in_time = validated_data.get('check_in_time') or timezone.now()

        attendance, created = Attendance.objects.update_or_create(
            student=student,
            date=today,
            defaults={
                'school': student.school,
                'classroom': student.classroom,
                'check_in_time': check_in_time,
                'status': validated_data.get('status', AttendanceStatus.PRESENT),
                'marked_by': request.user,
                'face_match_confidence': validated_data.get('face_match_confidence'),
                'capture_photo': validated_data.get('capture_photo'),
                'notes': validated_data.get('notes', ''),
            },
        )
        attendance._was_created = created
        return attendance


class BulkMarkAttendanceSerializer(serializers.Serializer):
    """Mark attendance for multiple students at once (manual fallback)."""

    date = serializers.DateField(required=False)
    records = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )

    def validate_date(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError('Date cannot be in the future.')
        return value

    def validate_records(self, value):
        profile = self.context['request'].user.headmaster_profile
        errors = []

        for i, record in enumerate(value):
            student_id = record.get('student_id')
            status = record.get('status', AttendanceStatus.PRESENT)

            if not student_id:
                errors.append({i: 'student_id is required.'})
                continue

            if status not in AttendanceStatus.values:
                errors.append({i: f'Invalid status: {status}.'})
                continue

            if not Student.objects.filter(
                pk=student_id,
                school_id=profile.school_id,
                is_active=True,
            ).exists():
                errors.append({i: f'Student {student_id} not found.'})

        if errors:
            raise serializers.ValidationError(errors)

        return value


class ClassAttendanceSummarySerializer(serializers.Serializer):
    classroom_id = serializers.IntegerField()
    classroom_name = serializers.CharField()
    date = serializers.DateField()
    total_students = serializers.IntegerField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    half_day = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()


class StudentAttendanceSummarySerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    roll_number = serializers.CharField()
    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    late_days = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
