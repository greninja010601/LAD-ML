import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testProject.settings')  # 🖊️ Replace your_project_name
django.setup()

import pandas as pd
import joblib
from collections import defaultdict
from datetime import timedelta

from testApp.models import AssignmentGroup, Assignment, Grade, Course

# --- Step 1: Setup ---
# Replace with your Online course_id (CS165-801)
online_course_id = 186019  # 🖊️ Replace with real online course_id

# --- Step 2: Group ID Mapping ---
group_mapping = {
    585140: 584767,  # Module Exams
    585141: 584768,  # Quizzes & Participation
    585142: 584769,  # zyBooks Reading Assignments
    585143: 584770,  # Programming Assignments
    585145: 584771,  # Lab Checkin
    585146: 584772   # Final Exam
}

# Expected Features for the model
expected_features = [
    'group_561368', 'group_561367', 'group_561372', 'group_561370', 'group_561369',  # Spring groups
    'group_584768', 'group_584767', 'group_584771', 'group_584770', 'group_584769', 'group_584772'  # Fall groups
]

# --- Step 3: Compute 20% Cutoff Date ---
course = Course.objects.get(course_id=online_course_id)
start_date = course.start_date
end_date = course.end_date
duration_days = (end_date - start_date).days
cutoff_date = start_date + timedelta(days=int(duration_days * 0.2))

print(f"\n📅 Course Start: {start_date.date()} | End: {end_date.date()} | 20% Cutoff: {cutoff_date.date()}")

# --- Step 4: Prepare Online Students Features ---

# Fetch Assignments that are due on or before the cutoff date
assignments = Assignment.objects.filter(course__course_id=online_course_id, due_at__lte=cutoff_date)

# Build Assignment to Group Mapping
assignment_to_group = {}
for assignment in assignments:
    if assignment.assignment_group:
        assignment_to_group[assignment.assignment_id] = assignment.assignment_group.group_id

# Fetch Grades only for these assignments
grades = Grade.objects.filter(assignment__in=assignments)

# Aggregate Scores per Student
student_scores = defaultdict(lambda: defaultdict(float))
student_total_possible = defaultdict(lambda: defaultdict(float))

for grade in grades:
    assignment = grade.assignment
    group_id = assignment_to_group.get(assignment.assignment_id)
    if group_id is None:
        continue
    
    mapped_gid = group_mapping.get(group_id)
    if mapped_gid is None:
        continue  # skip groups like 'Assignments' (not mapped)
    
    if assignment.points_possible:
        student_scores[grade.student.student_id][mapped_gid] += (grade.score or 0)
        student_total_possible[grade.student.student_id][mapped_gid] += assignment.points_possible

# Build Final Feature Set
prepared_students = []

for student_id, group_scores in student_scores.items():
    row = {'student_id': student_id}
    for mapped_gid, score in group_scores.items():
        total_possible = student_total_possible[student_id][mapped_gid]
        normalized_score = (score / total_possible) * 100 if total_possible > 0 else 0.0
        row[f"group_{mapped_gid}"] = normalized_score
    prepared_students.append(row)

X_online = pd.DataFrame(prepared_students)

# --- Step 5: Fill Missing Expected Features ---
for feature in expected_features:
    if feature not in X_online.columns:
        X_online[feature] = 0.0

# Drop student_id for prediction
X_online_final = X_online.drop(columns=['student_id'])

# Make sure column order matches
X_online_final = X_online_final[sorted(X_online_final.columns)]

# --- Step 6: Load Model and Predict ---
model = joblib.load('cs165_combined_model_20.pkl')
predicted_scores = model.predict(X_online_final)

# --- Step 7: Display Predictions ---
for idx, row in X_online.iterrows():
    print(f"👤 Student ID: {row['student_id']} ➔ 🎯 Predicted Final Score: {predicted_scores[idx]:.2f}")
