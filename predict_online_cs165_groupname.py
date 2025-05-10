# predict_online_cs165_groupname.py

import os
import django
import pandas as pd
import joblib
from collections import defaultdict
from datetime import timedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# --- Django Setup ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testProject.settings')
django.setup()

from testApp.models import Course, AssignmentGroup, Assignment, Grade, Enrollment

# --- Helper Functions ---
def compute_cutoff(course, progress_ratio):
    duration = (course.end_date - course.start_date).days
    return course.start_date + timedelta(days=int(duration * progress_ratio))

def prepare_online_student_data_groupname(course_id, progress_ratio):
    """
    Prepares feature matrix (X) for online students using group NAMES.
    Also tries to retrieve real final_score if available (for evaluation).
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

        # Also retrieve current_score if available (for evaluation)
        try:
            enrollment = Enrollment.objects.get(student__student_id=student_id, course=course)
            if enrollment.current_score is not None:
                row['final_score'] = enrollment.current_score
        except Enrollment.DoesNotExist:
            pass

        processed_data.append(row)

    df = pd.DataFrame(processed_data)
    df = df.fillna(0)

    print(f"\n✅ Prepared {len(df)} online students with group-name-based features.\n")
    return df

# --- Main Prediction + Evaluation ---
def main():
    # 🛠 SETTINGS
    online_course_id = 186019  # 🔥
    model_filename = 'cs165_combined_model_20_groupname.pkl'  # 🔥
    progress_ratio = 0.2  # 🔥 0.2 for 20%, or 0.5 for 50%

    # Load model
    model = joblib.load(model_filename)
    print(f"📂 Loaded model: {model_filename}")

    # Prepare online students data
    df = prepare_online_student_data_groupname(course_id=online_course_id, progress_ratio=progress_ratio)

    # Extract student IDs
    student_ids = df['student_id']

    # Expected features
    expected_features = model.get_booster().feature_names
    for col in expected_features:
        if col not in df.columns:
            df[col] = 0

    X_features = df[expected_features]

    # Predict
    predicted_scores = model.predict(X_features)

    # --- Output predictions ---
    print("\n🎯 Predicted Final Scores for Online Students:\n")
    for student_id, pred in zip(student_ids, predicted_scores):
        print(f"Student {student_id} → Predicted Final Score: {pred:.2f}")

    # --- Evaluation (if ground truth exists) ---
    if 'final_score' in df.columns:
        y_true = df['final_score']
        y_pred = predicted_scores

        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)

        print("\n📊 Evaluation Metrics (based on available current scores):")
        print(f" - Mean Absolute Error (MAE): {mae:.2f}")
        print(f" - Mean Squared Error (MSE): {mse:.2f}")
        print(f" - R² Score: {r2:.4f}")
    else:
        print("\n⚠️ No real final scores available for evaluation.")

if __name__ == "__main__":
    main()
