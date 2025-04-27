# utils.py
def calculate_score_and_letter_grade(student_id, course_id):
    from .models import Assignment, Grade, AssignmentGroup

    assignments = Assignment.objects.filter(course__course_id=course_id).select_related('assignment_group')
    assignment_groups = AssignmentGroup.objects.filter(course__course_id=course_id)

    total_weighted_score = 0
    total_weights = 0

    for group in assignment_groups:
        group_assignments = assignments.filter(assignment_group=group)
        total_earned = 0
        total_possible = 0

        for assignment in group_assignments:
            grade = Grade.objects.filter(student__student_id=student_id, assignment=assignment).first()
            if grade and grade.score is not None:
                total_earned += grade.score
                total_possible += assignment.points_possible

        if total_possible > 0:
            percentage = (total_earned / total_possible) * 100
            weighted_contribution = (percentage * group.group_weight) / 100
            total_weighted_score += weighted_contribution
            total_weights += group.group_weight

    final_score = round(total_weighted_score if total_weights > 0 else 0, 2)

    # Grade scale mapping
    if final_score >= 93:
        final_grade = "A"
    elif final_score >= 90:
        final_grade = "A-"
    elif final_score >= 87:
        final_grade = "B+"
    elif final_score >= 83:
        final_grade = "B"
    elif final_score >= 80:
        final_grade = "B-"
    elif final_score >= 77:
        final_grade = "C+"
    elif final_score >= 73:
        final_grade = "C"
    elif final_score >= 70:
        final_grade = "C-"
    elif final_score >= 67:
        final_grade = "D+"
    elif final_score >= 63:
        final_grade = "D"
    elif final_score >= 60:
        final_grade = "D-"
    else:
        final_grade = "F"

    return final_score, final_grade
