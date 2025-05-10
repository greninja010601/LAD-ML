# predict_online_cs165.py

import os
import django
import pandas as pd
import joblib
from collections import defaultdict
from datetime import timedelta

# --- Django Setup ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testProject.settings')  # Replace if your settings.py path is different
django.setup()

from testApp.models import Course, AssignmentGroup, Assignment, Grade

# --- Helper Functions ---
def compute_cutoff(course, progress_ratio):
    duration = (course.end_date - course.start_date).days
    return course.start_date + timedelta(days=int(duration * progress_ratio))

def prepare_online_student_data(course_id, progress_ratio):
    """
    Prepares feature matrix (X) for online students using assignment group NAMES (not IDs).
    """
    course = Course.objects.get(course_id=course_id)
    cutoff = compute_cutoff(course, progress_ratio)

    print(f"\n📘 Course: {course.course_name}")
    print(f" Start: {course.start_date.date()} | End: {course.end_date.date()}")
    print(f"⏱ Cutoff ({int(progress_ratio * 100)}%): {cutoff.date()}")

    assignment_groups = AssignmentGroup.objects.filter(course=course)
    group_id_to_name = {group.group_id: group.name for group in assignment_groups}

    assignments = Assignment.objects.filter(course=course, due_at__lte=cutoff)
    assignment_map = {a.assignment_id: a for a in assignments}

    grades = Grade.objects.filter(assignment_id__in=assignment_map.keys())

    student_features = defaultdict(lambda: defaultdict(float))
    student_total_points = defaultdict(lambda: defaultdict(float))

    for grade in grades:
        assignment = assignment_map[grade.assignment.assignment_id]
        if assignment.assignment_group is None:
            continue
        group_id = assignment.assignment_group.group_id
        if assignment.points_possible:
            group_name = group_id_to_name.get(group_id)
            if group_name:
                student_features[grade.student.student_id][group_name] += grade.score or 0
                student_total_points[grade.student.student_id][group_name] += assignment.points_possible

    processed_data = []

    for student_id, group_scores in student_features.items():
        row = {'student_id': student_id}
        for group_name, score in group_scores.items():
            total_possible = student_total_points[student_id][group_name]
            normalized_score = (score / total_possible) if total_possible > 0 else 0
            row[group_name] = normalized_score
        processed_data.append(row)

    df = pd.DataFrame(processed_data)
    df = df.fillna(0)

    print(f"\n✅ Prepared {len(df)} online students with group-name-based features.\n")
    return df

# --- Main Prediction Flow ---
def main():
    # 🛠 SETTINGS (Change here)
    online_course_id = 186019  # 🔥 Set your online course ID here
    model_filename = 'cs165_combined_model_20.pkl'  # 🔥 Set your trained model filename here
    progress_ratio = 0.2  # 🔥 0.2 for 20%, or 0.5 for 50%

    # Load model
    print(f"📂 Loading model: {model_filename}")
    model = joblib.load(model_filename)

    # Prepare online student data
    X_online = prepare_online_student_data(course_id=online_course_id, progress_ratio=progress_ratio)

    # Extract student IDs
    student_ids = X_online['student_id']

    # --- Expected features based on group names ---
    expected_features = [
        'Quizzes & participation',
        'Module Exams',
        'Lab Checkin',
        'Programming Assignments',
        'zyBooks Reading Assignments'
    ]

    # Align feature columns
    for col in expected_features:
        if col not in X_online.columns:
            X_online[col] = 0

    # Final feature matrix (drop student_id, only model features)
    X_features = X_online[expected_features]

    # Predict
    predicted_scores = model.predict(X_features)

    # --- Output ---
    print("\n🎯 Predicted Final Scores for Online Students:\n")
    for student_id, pred in zip(student_ids, predicted_scores):
        print(f"Student {student_id} → Predicted Final Score: {pred:.2f}")

if __name__ == "__main__":
    main()
