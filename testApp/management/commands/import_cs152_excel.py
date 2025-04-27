# testApp/management/commands/import_cs152_excel.py

import pandas as pd
import re
from django.core.management.base import BaseCommand
from testApp.models import Course, Student, Enrollment, Assignment, Grade, AssignmentGroup
from django.db.models import Q

class Command(BaseCommand):
    help = 'Import CS152 Spring CSV data (labs, modules, exams, final grade) into Django DB safely'

    def handle(self, *args, **kwargs):
        csv_path = 'testApp/data/Grades-2024SP-CS-152-001.csv'

        course, _ = Course.objects.get_or_create(course_id=5243300, defaults={
            'course_name': "CS152",
            'term': "Spring2024"
        })

        group_keywords = {
            "Labs": ["Lab"],
            "Knowledge Checks": ["Module", "Knowledge Check"],
            "Coding Exams": ["Coding Exam"],
            "Regular Exams": ["Exam"]
        }

        df = pd.read_csv(csv_path)

        print("Columns in CSV:", df.columns.tolist())

        assignment_columns = [col for col in df.columns if re.search(r"\(\d+\)", col)]
        final_score_col = next((col for col in df.columns if "final score" in col.lower() and "formative" not in col.lower()), None)
        final_grade_col = next((col for col in df.columns if "final grade" in col.lower()), None)

        print("Detected assignment columns:", assignment_columns)
        print("Detected final score column:", final_score_col)
        print("Detected final grade column:", final_grade_col)

        student_count = 0
        enrollment_count = 0
        assignment_count = 0
        grade_count = 0

        for _, row in df.iterrows():
            student_id = str(row.get("ID", "")).strip()
            if not student_id:
                continue

            student, created_student = Student.objects.get_or_create(student_id=student_id)
            if created_student:
                student_count += 1

            enrollment_qs = Enrollment.objects.filter(student=student, course=course)
            if enrollment_qs.exists():
                enrollment = enrollment_qs.first()
            else:
                enrollment = Enrollment.objects.create(student=student, course=course, role="StudentEnrollment")
                enrollment_count += 1

            try:
                if final_score_col and pd.notna(row[final_score_col]):
                    try:
                        enrollment.current_score = float(row[final_score_col])
                    except ValueError:
                        self.stderr.write(f"⚠️ Score not float for {student_id}, skipping score.")
                if final_grade_col and pd.notna(row[final_grade_col]):
                    enrollment.current_grade = str(row[final_grade_col]).strip()
                enrollment.save()
            except Exception as e:
                self.stderr.write(f"⚠️ Error setting final score/grade for {student_id}: {e}")

            for col in assignment_columns:
                match = re.search(r"\((\d+)\)", col)
                if not match:
                    continue
                assignment_id = int(match.group(1))
                assignment_name = col.split("(")[0].strip()

                group_name = "Ungrouped"
                for gname, keywords in group_keywords.items():
                    if any(kw.lower() in assignment_name.lower() for kw in keywords):
                        group_name = gname
                        break

                group, _ = AssignmentGroup.objects.get_or_create(
                    name=group_name,
                    course=course,
                    defaults={"group_weight": 0.0}
                )

                assignment, created_assignment = Assignment.objects.get_or_create(
                    assignment_id=assignment_id,
                    defaults={
                        'name': assignment_name,
                        'assignment_group': group,
                        'course': course,
                        'points_possible': 100
                    }
                )
                if created_assignment:
                    assignment_count += 1

                try:
                    score = float(row[col])
                    _, created_grade = Grade.objects.update_or_create(
                        student=student,
                        assignment=assignment,
                        defaults={"score": score}
                    )
                    if created_grade:
                        grade_count += 1
                except Exception as e:
                    print(f"Skipping grade for {student_id} - {col}: {e}")
                    continue

        if student_count + assignment_count + grade_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Import complete: {student_count} students, {enrollment_count} enrollments, {assignment_count} assignments, {grade_count} grades added."))
        else:
            self.stderr.write(self.style.WARNING("⚠️ No data was imported. Please check your CSV content and format."))
