from rest_framework import serializers

from schools.models import ClassRoom, School


class SchoolSerializer(serializers.ModelSerializer):
    classroom_count = serializers.IntegerField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = School
        fields = [
            'id', 'name', 'address', 'city', 'state', 'pincode',
            'phone', 'email', 'logo', 'is_active',
            'classroom_count', 'student_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                'School name must be at least 2 characters.'
            )
        return value.strip()

    def validate_phone(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Phone number is required.')
        return cleaned


class SchoolCreateSerializer(SchoolSerializer):
    class Meta(SchoolSerializer.Meta):
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_active']


class ClassRoomSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ClassRoom
        fields = [
            'id', 'school', 'school_name', 'name', 'grade', 'section',
            'academic_year', 'is_active', 'student_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_grade(self, value):
        if not value.strip():
            raise serializers.ValidationError('Grade is required.')
        return value.strip()

    def validate_academic_year(self, value):
        if '-' not in value:
            raise serializers.ValidationError(
                'Academic year should be in format YYYY-YYYY (e.g. 2025-2026).'
            )
        return value.strip()

    def validate(self, attrs):
        school = attrs.get('school') or (
            self.instance.school if self.instance else None
        )
        grade = attrs.get('grade', getattr(self.instance, 'grade', None))
        section = attrs.get('section', getattr(self.instance, 'section', ''))
        academic_year = attrs.get(
            'academic_year',
            getattr(self.instance, 'academic_year', None),
        )

        if school and grade and academic_year:
            qs = ClassRoom.objects.filter(
                school=school,
                grade=grade,
                section=section or '',
                academic_year=academic_year,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    'A classroom with this grade, section, and academic year already exists.'
                )

        return attrs
