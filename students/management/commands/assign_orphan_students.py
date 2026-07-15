"""
Assign students with missing classroom to a classroom.
Run on PythonAnywhere:
  python manage.py assign_orphan_students
"""

from django.core.management.base import BaseCommand

from schools.models import ClassRoom
from students.models import Student


class Command(BaseCommand):
    help = 'Assign students with no classroom to the first classroom of their school'

    def handle(self, *args, **options):
        orphans = Student.objects.filter(classroom__isnull=True, is_active=True)
        total = orphans.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No orphan students found.'))
            return

        fixed = 0
        skipped = 0
        for student in orphans:
            classroom = ClassRoom.objects.filter(
                school_id=student.school_id,
                is_active=True,
            ).order_by('id').first()
            if not classroom:
                skipped += 1
                self.stdout.write(
                    f'Skip {student}: no classroom in school {student.school_id}'
                )
                continue
            student.classroom = classroom
            student.save(update_fields=['classroom', 'updated_at'])
            fixed += 1
            self.stdout.write(
                f'Assigned {student.full_name} → {classroom.name}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Fixed={fixed}, Skipped={skipped}, Total orphans={total}'
            )
        )
