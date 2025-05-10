# train_cs165_groupname.py

import os
import django
import pandas as pd
import joblib
from xgboost import XGBRegressor
from collections import defaultdict
from datetime import timedelta

# --- Django Setup ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testProject.settings')  # Replace with your settings path
django.setup()

from testApp.models import Course, AssignmentGroup, Assignment, Grade, Enrollment

# --- Helper Functions ---
def compute_cutoff(course, progress_ratio):
    duration = (course.end_date - course.start_date).days
    return course.start_date + timedelta(days=int(duration * progress_ratio))

def prepare_training_data_groupname(course_id, progress_ratio):
    """
    Prepares feature matrix using group NAMES for training.
    """
    course = Course.objects.get(course_id=course_id)
    cutoff = compute_cutoff(course, progress_ratio)

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
        try:
            enrollment = Enrollment.objects.get(student__student_id=student_id, course=course)
            if enrollment.current_score is not None:
                row['final_score'] = enrollment.current_score
                processed_data.append(row)
        except Enrollment.DoesNotExist:
            continue

    df = pd.DataFrame(processed_data)
    df = df.fillna(0)

    print(f"\n✅ Prepared training data for {len(df)} students with group names.\n")
    return df

def prepare_combined_training_data_groupname(spring_course_id, fall_course_id, progress_ratio):
    spring_df = prepare_training_data_groupname(course_id=spring_course_id, progress_ratio=progress_ratio)
    fall_df = prepare_training_data_groupname(course_id=fall_course_id, progress_ratio=progress_ratio)

    combined_df = pd.concat([spring_df, fall_df], ignore_index=True)
    print(f"\n✅ Combined Group-Name DataFrame: {len(combined_df)} students total.\n")
    return combined_df

# --- Main Training Function ---
def main():
    # 🛠 SETTINGS (Change here)
    spring_course_id = 177318 # 🔥
    fall_course_id = 187540      # 🔥
    progress_ratio = 0.5  # 🔥 0.2 for 20%, or 0.5 for 50%

    # Prepare data
    df = prepare_combined_training_data_groupname(spring_course_id, fall_course_id, progress_ratio)

    # Separate features and label
    X = df.drop(columns=['student_id', 'final_score'])
    y = df['final_score']

    # Train model
    model = XGBRegressor()
    model.fit(X, y)

    # Save model
    model_filename = 'cs165_combined_model_50_groupname.pkl'
    joblib.dump(model, model_filename)

    print(f"\n🎯 Model trained and saved to {model_filename}")

if __name__ == "__main__":
    main()
