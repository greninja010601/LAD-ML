def calculate_score_and_letter_grade(student, course):
    from .models import Assignment, Grade, AssignmentGroup

    print("🎯 Using FINALIZED screen_10-based calculator")

    assignments = Assignment.objects.filter(course=course)
    grades = Grade.objects.filter(student=student, assignment__in=assignments)
    groups = AssignmentGroup.objects.filter(course=course)

    total_weighted_score = 0
    total_weight = 0

    for group in groups:
        group_assignments = assignments.filter(assignment_group=group)
        total_score = 0
        total_possible = 0
        weight = group.group_weight or 0

        for assignment in group_assignments:
            if assignment.points_possible is None:
                continue  # 🚫 skip assignments without valid points

            grade = grades.filter(assignment=assignment).first()
            score = grade.score if grade and grade.score is not None else 0
            total_score += score
            total_possible += assignment.points_possible

        if total_possible > 0:
            percentage = (total_score / total_possible) * 100
            weighted_score = (percentage * weight) / 100
            total_weighted_score += weighted_score
            total_weight += weight

    if total_weight > 0:
        final_score = round((total_weighted_score / total_weight), 2) * 100
    else:
        final_score = None

    if final_score is None:
        final_grade = None
    elif final_score >= 93:
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
