import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testProject.settings')  # << your project name (folder with settings.py)
django.setup()

from datetime import timedelta
from collections import defaultdict
import pandas as pd

from testApp.models import Course, AssignmentGroup, Assignment, Grade, Enrollment

# --- Compute cutoff date based on progress ---
def compute_cutoff(course, progress_ratio):
    duration = (course.end_date - course.start_date).days
    return course.start_date + timedelta(days=int(duration * progress_ratio))

# --- Prepare training data for a single course ---
def prepare_training_data(course_id, progress_ratio):
    course = Course.objects.get(course_id=course_id)
    cutoff = compute_cutoff(course, progress_ratio)

    print(f"\n📘 Course: {course.course_name}")
    print(f" Start: {course.start_date.date()} | End: {course.end_date.date()}")
    print(f"⏱ Cutoff ({int(progress_ratio * 100)}%): {cutoff.date()}")

    assignment_groups = AssignmentGroup.objects.filter(course=course)
    group_weights = {group.group_id: group.group_weight for group in assignment_groups}

    # Print assignment group summary
    print(f"\n Assignment Groups (group_id → weight):")
    for gid, weight in group_weights.items():
        print(f" - group_{gid}: {weight}")

    assignments = Assignment.objects.filter(course=course, due_at__lte=cutoff)
    assignment_map = {a.assignment_id: a for a in assignments}

    print(f"\n Assignments before cutoff ({cutoff.date()}): {len(assignments)}")
    for a in assignments:
        print(f" - {a.name} | Due: {a.due_at.date() if a.due_at else 'N/A'} | Group: {a.assignment_group.group_id if a.assignment_group else 'None'}")

    grades = Grade.objects.filter(assignment_id__in=assignment_map.keys())

    student_features = defaultdict(lambda: defaultdict(float))
    student_total_points = defaultdict(lambda: defaultdict(float))

    print(f"\n📥 Processing Grades for {len(grades)} submissions...")

    for grade in grades:
        assignment = assignment_map[grade.assignment.assignment_id]
        if assignment.assignment_group is None:
            continue
        group_id = assignment.assignment_group.group_id
        if assignment.points_possible:
            student_features[grade.student.student_id][group_id] += grade.score or 0
            student_total_points[grade.student.student_id][group_id] += assignment.points_possible

    print("\n📦 Aggregating features per student...")
    processed_data = []

    for student_id, group_scores in student_features.items():
        row = {'student_id': student_id}
        print(f"\n👤 Student: {student_id}")
        for group_id, score in group_scores.items():
            total_possible = student_total_points[student_id][group_id]
            weight = group_weights.get(group_id, 0)
            normalized_score = (score / total_possible) * weight if total_possible > 0 else 0
            row[f"group_{group_id}"] = normalized_score
            print(f"   - group_{group_id}: score={score}, total={total_possible}, weight={weight} → normalized={normalized_score:.2f}")

        try:
            enrollment = Enrollment.objects.get(student__student_id=student_id, course=course)
            if enrollment.current_score is not None:
                row['final_score'] = enrollment.current_score
                processed_data.append(row)
        except Enrollment.DoesNotExist:
            continue

    df = pd.DataFrame(processed_data)
    df = df.fillna(0)

    print(f"\n✅ Final DataFrame: {len(df)} students × {df.shape[1]-2} groups + final_score\n")
    return df

# --- NEW: Prepare combined training data from two courses (Spring + Fall) ---
def prepare_combined_training_data(spring_course_id, fall_course_id, progress_ratio):
    """
    Prepares and merges data from both Spring and Fall courses based on progress cutoff.
    """
    print("\n🚀 Preparing Spring Data...")
    spring_df = prepare_training_data(course_id=spring_course_id, progress_ratio=progress_ratio)

    print("\n🚀 Preparing Fall Data...")
    fall_df = prepare_training_data(course_id=fall_course_id, progress_ratio=progress_ratio)

    combined_df = pd.concat([spring_df, fall_df], ignore_index=True)

    print(f"\n✅ Combined DataFrame: {len(combined_df)} students total.\n")
    return combined_df
