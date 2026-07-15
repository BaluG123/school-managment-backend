from rest_framework import serializers

from core.validators import validate_image_file
from schools.models import ClassRoom, School
from students.models import Student


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'school', 'school_name', 'classroom', 'classroom_name',
            'first_name', 'last_name', 'full_name', 'roll_number',
            'admission_number', 'date_of_birth', 'gender',
            'parent_name', 'parent_phone', 'address',
            'face_photo', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'school', 'school_name', 'classroom_name',
            'full_name', 'created_at', 'updated_at',
        ]

    def validate_face_photo(self, value):
        if value:
            validate_image_file(value)
        return value

    def validate_first_name(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError('First name is required.')
        return value.strip()

    def validate_last_name(self, value):
        return value.strip()

    def validate_roll_number(self, value):
        if not value.strip():
            raise serializers.ValidationError('Roll number is required.')
        return value.strip()

    def validate_admission_number(self, value):
        if not value.strip():
            raise serializers.ValidationError('Admission number is required.')
        return value.strip()

    def validate(self, attrs):
        request = self.context.get('request')
        profile = getattr(getattr(request, 'user', None), 'headmaster_profile', None)

        school = attrs.get('school')
        if not school and self.instance:
            school = self.instance.school
        if not school and profile and profile.school_id:
            school = profile.school

        classroom = attrs.get('classroom')
        roll_number = attrs.get(
            'roll_number',
            getattr(self.instance, 'roll_number', None),
        )
        admission_number = attrs.get(
            'admission_number',
            getattr(self.instance, 'admission_number', None),
        )

        if classroom and school and classroom.school_id != school.id:
            raise serializers.ValidationError({
                'classroom': 'Classroom must belong to the same school.',
            })

        if school and roll_number:
            qs = Student.objects.filter(school=school, roll_number=roll_number)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'roll_number': 'A student with this roll number already exists in this school.',
                })

        if school and admission_number:
            qs = Student.objects.filter(
                school=school,
                admission_number=admission_number,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'admission_number': 'A student with this admission number already exists.',
                })

        return attrs


class StudentListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'roll_number', 'admission_number',
            'classroom', 'classroom_name', 'face_photo', 'is_active',
        ]


class StudentFacePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'full_name', 'face_photo']
        read_only_fields = ['id', 'full_name', 'face_photo']

    def validate_face_photo(self, value):
        validate_image_file(value)
        return value
