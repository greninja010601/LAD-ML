from django.http import HttpResponse,JsonResponse
from django.shortcuts import get_object_or_404, render
import requests,json,time,threading
from datetime import datetime, timedelta
from .models import *
from .models import Course, Student, Enrollment, AssignmentGroup, Assignment, Grade



# Global variable to store grades history
grades_history = []

def get_letter_grade(score):
    if score >= 93: return "A"
    elif score >= 90: return "A-"
    elif score >= 87: return "B+"
    elif score >= 83: return "B"
    elif score >= 80: return "B-"
    elif score >= 77: return "C+"
    elif score >= 73: return "C"
    elif score >= 70: return "C-"
    elif score >= 67: return "D+"
    elif score >= 63: return "D"
    elif score >= 60: return "D-"
    else: return "F"
# Create your views here.
def index(request):
    return render(request,'index.html')

def screen_1(request, course_id, course_name, student_name,user_id):
    return render(request, 'screen_1.html',{'students': student_name, 'course_id': course_id, 'course_name': course_name,'user_id':user_id})

def screen_2(request):
    return render(request, 'screen_2.html')

def screen_3(request):
    terms = [ 'Spring Semester 2024', 'Summer Semester 2024', 'Fall Semester 2024','Spring Semester 2025' ]
    return render(request, 'screen_3.html', {'terms': terms})

def screen_4(request):
    term = request.GET.get('term', '')
    return render(request, 'screen_4.html', {'term': term})


def screen_5(request, term):
    subject = request.GET.get('subject', '').strip().lower()
    course_number = request.GET.get('course_number', '').replace(" ", "").lower()

    courses_qs = Course.objects.all()

    # Extract year and term code from the full term string (e.g., "Spring Semester 2025")
    import re
    year_match = re.search(r'\d{4}', term)
    extracted_year = year_match.group(0) if year_match else ''
    term_type = ''
    if 'spring' in term.lower():
        term_type = 'SP'
    elif 'fall' in term.lower():
        term_type = 'FA'
    elif 'summer' in term.lower():
        term_type = 'SU'

    # Build expected term prefix like "2024FA"
    expected_term_prefix = f"{extracted_year}{term_type}"

    # Case 1: No filters — show courses matching the selected term prefix
    if not subject and not course_number:
        courses_qs = courses_qs.filter(course_name__istartswith=expected_term_prefix)

    # Case 2: Subject keyword search (e.g., "introduction" or "java")
    if subject:
        courses_qs = courses_qs.filter(course_name__icontains=subject)

    # Case 3: Course number search (e.g., "cs 150" or "cs150")
    if course_number:
        normalized_qs = []
        for course in courses_qs:
            normalized_code = course.course_code.replace(" ", "").lower()
            if course_number in normalized_code:
                normalized_qs.append(course)
        courses_qs = normalized_qs

    # Collect courses and instructor info
    courses = []
    unique_instructors = set()

    for course in courses_qs:
        if course.instructor:
            unique_instructors.add(course.instructor)
        courses.append({
            'id': course.course_id,
            'name': course.course_name,
            'course_code': course.course_code,
            'instructor': course.instructor or "N/A"
        })

    return render(request, 'screen_5.html', {
        'courses': courses,
        'term': term,
        'total_courses': len(courses),
        'assigned_instructors': len(unique_instructors)
    })



def screen_6(request, course_id):
    # Get course from DB
    course = Course.objects.get(course_id=course_id)
    course_name = request.GET.get('course_name', course.course_name)

    # Fetch students enrolled in the course
    enrollments = Enrollment.objects.filter(course=course, role='StudentEnrollment').select_related('student')
    
    # Prepare list of students
    students = []
    for enrollment in enrollments:
        students.append({
            'name': enrollment.student.student_name,
            'user_id': enrollment.student.student_id
        })

    # Optional: Filter using search field
    search_query = request.GET.get('search_field', '')
    if search_query:
        students = [
            student for student in students
            if search_query.lower() in student['name'].lower()
        ]

    return render(request, 'screen_6.html', {
        'students': students,
        'course_id': course_id,
        'course_name': course_name
    })

def screen_7(request, course_id, course_name, student_name,user_id):
    screen_data = retrieve_data(course_id, course_name, student_name,user_id)
    return render(request, 'screen_7.html', screen_data)

def screen_8(request, course_id, course_name, student_name, user_id):
    import pandas as pd
    import joblib
    from .models import Course, Student, Enrollment

    accuracy_20 = round(0.607 * 100, 2)  # → 87.2%
    accuracy_50 = round(0.915 * 100, 2)  # → 91.5%

    course = Course.objects.get(course_id=course_id)
    student = Student.objects.get(student_id=user_id)

    predicted_score = None
    prediction_message = ""
    is_loading = False

    prediction_type = request.POST.get('prediction_type') or request.GET.get('prediction_type')

    if request.method == "POST":
        is_loading = True  # Start loading

        if prediction_type in ['20', '50'] and "data structures" in course.course_name.lower():
            try:
                model = joblib.load(f'cs165_combined_model_{prediction_type}_groupname.pkl')

                feature_dict = extract_student_features_by_group_name(
                    student_id=student.student_id,
                    course_id=course.course_id,
                    progress_ratio=float(prediction_type) / 100
                )
                feature_df = pd.DataFrame([feature_dict])

                expected_features = model.get_booster().feature_names
                for col in expected_features:
                    if col not in feature_df.columns:
                        feature_df[col] = 0
                feature_df = feature_df[expected_features]

                predicted_score = round(model.predict(feature_df)[0], 2)
                is_loading = False  # Stop loading after success
            except Exception as e:
                prediction_message = f"❌ Prediction failed: {str(e)}"
                is_loading = False
        else:
            prediction_message = "🚫 Prediction available only for Data Structures (CS165)."
            is_loading = False

    try:
        grade_info = Enrollment.objects.get(student=student, course=course)
    except Enrollment.DoesNotExist:
        grade_info = None

    return render(request, 'screen_8.html', {
        'student_name': student_name,
        'course_id': course_id,
        'course_name': course_name,
        'user_id': user_id,
        'grade_info': grade_info,
        'predicted_score': predicted_score,
        'prediction_type': prediction_type,
        'prediction_message': prediction_message,
        'is_loading': is_loading,
        'accuracy_20': accuracy_20,
        'accuracy_50': accuracy_50
    })







def screen_9(request, course_id, course_name, student_name, user_id):

    # update_student_grades(course_id, student_name, course_name,user_id)
    # update_all_students_grades()
    # Retrieve the weekly grades and category percentages
    grades = WeeklyGrade.objects.filter(
        student__student_id=user_id,
        course__course_id=course_id
    ).order_by('WeekNumber')
    
    # Convert the grades to a list of dictionaries
    hist_grade_data = [
        {
            'week': grade.WeekNumber,
            'grade': grade.PercentileGrade,
            'categorical_percentage':grade.categorized_assignment_grades
        }
        for grade in grades
    ]
    
    # Convert the grade data to JSON
    hist_grade_data_json = json.dumps(hist_grade_data)
    
 
    categorical_grades = WeeklyGrade.objects.filter(
        student__student_id=user_id,
        course__course_id=course_id
    ).order_by('WeekNumber').values_list('WeekNumber', 'categorized_assignment_grades')
    

    categorical_grade_data = [
        {
            'week': week,
            'category_scores': json.loads(score)
        }
        for week, score in categorical_grades
    ]
    
    categorical_grade_data_json = json.dumps(categorical_grade_data)
    
    screen_data = retrieve_data(course_id, course_name, student_name, user_id)
    
    screen_data['hist_grade_data_json'] = hist_grade_data_json
    screen_data['categorical_grade_data_json']= categorical_grade_data_json
    print(hist_grade_data_json)
    return render(request, 'screen_9.html', screen_data)

def calendar_view(request):
    return render(request, 'calendar_screen.html')


def screen_10(request, course_id, student_id):
    course = Course.objects.get(course_id=course_id)
    student = Student.objects.get(student_id=student_id)
    assignments = Assignment.objects.filter(course=course)
    grades = Grade.objects.filter(student=student, assignment__in=assignments)
    groups = AssignmentGroup.objects.filter(course=course)

    category_data = []
    total_weighted_score = 0
    total_weight = 0

    for group in groups:
        group_assignments = assignments.filter(assignment_group=group)
        total_score = 0
        total_possible = 0
        weight = group.group_weight or 0

        for assignment in group_assignments:
            grade = grades.filter(assignment=assignment).first()
            score = grade.score if grade else 0
            total_score += score or 0
            total_possible += assignment.points_possible

        if total_possible > 0:
            percentage = (total_score / total_possible) * 100
            weighted_score = (percentage * weight) / 100
            total_weighted_score += weighted_score
            total_weight += weight
            category_data.append((group.name, percentage, weight))
        else:
            category_data.append((group.name, None, weight))

    if total_weight > 0:
        final_grade = round((total_weighted_score / total_weight), 2)
    else:
        final_grade = None

    return render(request, 'screen_10.html', {
        'student': student,
        'course': course,
        'category_data': category_data,
        'final_grade': final_grade
    })


import requests
from django.http import JsonResponse

def test_token(request):
    token = "3716~eFecnK3f2cDrkawtPCRPvVJCLvNDUE2yZZDkKZDWEv4uH36vrzCEeJf4T4QrhNQW"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    base_url = "https://colostate.instructure.com/api/v1"
    courses_url = f"{base_url}/courses?state[]=all&enrollment_type[]=teacher&per_page=100"

    all_courses = []
    while courses_url:
        response = requests.get(courses_url, headers=headers)
        if response.status_code != 200:
            break
        all_courses.extend(response.json())

        # Handle pagination via 'Link' header
        next_link = response.links.get('next')
        courses_url = next_link['url'] if next_link else None

    # Filter courses with keywords like "2024", "CS152", etc.
    filtered_courses = [
        {"id": c.get("id"), "name": c.get("name")}
        for c in all_courses
    ]

    # Get user info
    user_response = requests.get(f"{base_url}/users/self", headers=headers)
    user_data = user_response.json() if user_response.status_code == 200 else {}

    return JsonResponse({
        "status": "valid",
        "user": user_data,
        "total_courses_checked": len(all_courses),
        "matched_courses": filtered_courses
    })

    
def retrieve_data(course_id, course_name, student_name, user_id):
    try:
        course = Course.objects.get(course_id=course_id)
        student = Student.objects.get(student_id=user_id)
    except (Course.DoesNotExist, Student.DoesNotExist):
        return {
            'error': "Course or student not found.",
            'course_name': course_name,
            'student_name': student_name,
        }

    categorized_assignment_grades = {}
    category_percentages = {}
    assignment_statistics = []

    groups = AssignmentGroup.objects.filter(course=course)
    for group in groups:
        group_name = group.name
        group_assignments = Assignment.objects.filter(course=course, assignment_group=group)
        assignments_data = []
        total_score = 0
        total_possible = 0

        for assignment in group_assignments:
            grade = Grade.objects.filter(assignment=assignment, student=student).first()
            score = grade.score if grade else None
            stats = fetch_assignment_stats_from_db(assignment)

            if score is not None:
                total_score += score
            if assignment.points_possible is not None:
                total_possible += assignment.points_possible

            assignments_data.append({
                'name': assignment.name,
                'grade': score,
                'points_possible': assignment.points_possible,
                'score_statistics': stats
            })

        percentage = (total_score / total_possible) * 100 if total_possible > 0 else 0
        category_percentages[group_name] = percentage
        categorized_assignment_grades[group_name] = {
            'assignments': assignments_data,
            'total_points_possible': total_possible
        }

    # Fetch current grade info from Enrollment
    try:
        enrollment = Enrollment.objects.get(student=student, course=course, role='StudentEnrollment')
        grade_info = {
            'current_grade': enrollment.current_grade,
            'current_score': enrollment.current_score,
        }
    except Enrollment.DoesNotExist:
        grade_info = None

    # Risk factors (optional reuse)
    assignment_groups_weightages, individual_risk_factors, overall_risk_factor, weighted_scores = risk_factors_from_db(course, category_percentages)

    return {
        'course_name': course_name,
        'student_name': student_name,
        'categorized_assignment_grades': categorized_assignment_grades,
        'category_percentages': category_percentages,
        'grade_info': grade_info,
        'individual_risk_factors': individual_risk_factors,
        'overall_risk_factor': overall_risk_factor,
        'weighted_scores': weighted_scores,
        'assignment_groups_weightages': assignment_groups_weightages,
        'weighted_scores_json': json.dumps(categorized_assignment_grades),
        'total_weighted_scores_json': json.dumps(weighted_scores),
        'assignment_groups_weightages_json': json.dumps(assignment_groups_weightages),
    }



def fetch_assignment_stats_from_db(assignment):
    scores = Grade.objects.filter(assignment=assignment).exclude(score__isnull=True).values_list('score', flat=True)
    if not scores:
        return None

    scores = list(scores)
    return {
        'mean_score': sum(scores) / len(scores),
        'max_score': max(scores),
        'min_score': min(scores),
        'total_submissions': len(scores),
    }
        
def retrieve_all_assignments(course_id, headers):
    api_url = "https://canvas.instructure.com/api/v1/"
    all_assignments = []
    page = 1
    
    while True:
        response = requests.get(f"{api_url}courses/{course_id}/assignments?page={page}", headers=headers)
        if response.status_code == 200:
            assignments_data = response.json()
            all_assignments.extend(assignments_data)
            # Check if there are more pages
            if 'next' in response.links:
                page += 1
            else:
                break
        else:
            print("Failed to retrieve assignments:", response.status_code)
            break
            
    return all_assignments

from .models import AssignmentGroup

def risk_factors_from_db(course, category_percentages):
    assignment_groups_with_weightages = {}
    risk_factors = {}

    # Fetch assignment groups from the local DB
    assignment_groups = AssignmentGroup.objects.filter(course=course)

    for group in assignment_groups:
        group_name = group.name
        weight = group.group_weight or 0  # Use 0 if weight is None
        assignment_groups_with_weightages[group_name] = {'weight': weight}

        # Calculate risk factor
        percentage = category_percentages.get(group_name, 0)
        risk_factor = max((100 - percentage) / 100, 0) * weight
        risk_factors[group_name] = risk_factor

    # Overall risk factor = sum of all individual ones
    overall_risk_factor = sum(risk_factors.values())

    # Weighted scores calculation
    weighted_scores = {}
    total_weighted_score = 0
    for category, percentage in category_percentages.items():
        weightage = assignment_groups_with_weightages.get(category, {}).get('weight', 0)
        weighted_score = (percentage * weightage) / 100
        weighted_scores[category] = weighted_score
        total_weighted_score += weighted_score

    return assignment_groups_with_weightages, risk_factors, overall_risk_factor, weighted_scores


def fetch_all_courses(api_url, headers):
    courses = []
    page = 1
    while True:
        # Adjusting the URL to use the provided endpoint for courses
        response = requests.get(f"{api_url}courses?page={page}", headers=headers)
        if response.status_code == 200:
            
            fetched_courses = response.json()
            if not fetched_courses:
                break  # Exit the loop if no more courses are returned
            courses.extend(fetched_courses)
            page += 1
        else:
            print(f"Failed to fetch courses. Status Code: {response.status_code}")
            break
    return courses

def fetch_course_students(course_id, api_url, headers):
    students = []

    # Request the first page of enrollments data from the Canvas API
    response_enrollments = requests.get(f"{api_url}courses/{course_id}/enrollments?type[]=StudentEnrollment", headers=headers)

    if response_enrollments.status_code == 200:
        enrollments_data = response_enrollments.json()

        # Iterate through each enrollment record, filtering for students
        for enrollment in enrollments_data:
            if enrollment['type'] == 'StudentEnrollment':
                student_info = {
                    'name': enrollment['user']['name'],
                    'user_id': enrollment['user']['id']
                }
                students.append(student_info)
    else:
        print(f"Failed to fetch students for course {course_id}. Status Code: {response_enrollments.status_code}")
    return students

def update_all_students_grades():
    api_url = "https://canvas.instructure.com/api/v1/"
    headers = {
        "Authorization": "Bearer 7~o1bbKk1sCwslpRjwUz2AjqlgDsFVUkvKvtKinsgx57pBhqkumaWQFomPAuKCsNpP"
    }
    courses = fetch_all_courses(api_url, headers)  # You need to implement this based on your API
    for course in courses:
        course_id = course['id']
        course_name = course['name']
        print(course_name)
        students = fetch_course_students(course_id, api_url, headers)  # Implement this function to fetch students
        for student in students:
            student_name = student['name']
            user_id = student['user_id']
            print(student_name)
            # Now, you use your existing logic to update grades, adjusted to this loop
            update_student_grades(course_id, student_name, course_name, user_id)
            print("Done !")

def update_student_grades(course_id, student_name, course_name,user_id):
    # Assuming `api_url` and `headers` are defined elsewhere and are correct
    api_url = "https://canvas.instructure.com/api/v1/"

    # Authentication headers (replace with your API token or OAuth)
    headers = {
        "Authorization": "Bearer 7~o1bbKk1sCwslpRjwUz2AjqlgDsFVUkvKvtKinsgx57pBhqkumaWQFomPAuKCsNpP"
    }

    # Fetch the current week number since the start date
    
    week_number = 6

    context = retrieve_data(course_id, course_name, student_name, user_id)
    categorized_assignment_grades = context.get('categorized_assignment_grades', {})
    

    response_enrollment = requests.get(f"{api_url}courses/{course_id}/enrollments", headers=headers)
    if response_enrollment.status_code == 200:
        enrollments_data = response_enrollment.json()
        for enrollment in enrollments_data:
            if enrollment['user']['name'] == student_name:
                grade_info = {
                    'current_grade': enrollment.get('grades', {}).get('current_grade', ''),
                    'current_score': enrollment.get('grades', {}).get('current_score', ''),
                }
                category_percentages = {}
                for category, data in categorized_assignment_grades.items():
                    total_points_possible = data['total_points_possible']
                    total_score = sum(assignment['grade'] for assignment in data['assignments'] if assignment['grade'] is not None)
                    if total_points_possible != 0:
                        category_percentages[category] = (total_score / total_points_possible) * 100
                    else:
                        category_percentages[category] = 0

                category_percentages_json = json.dumps(category_percentages)
                # Update or create student information
                student, created = Student.objects.update_or_create(
                    student_id=user_id,
                    defaults={'student_name': student_name}
                )

                course, _ = Course.objects.get_or_create(
                    course_id=course_id,
                    defaults={'course_name': course_name}  # Assuming course_name is passed or retrieved
                )

                # Create a new weekly grade record
                WeeklyGrade.objects.update_or_create(
                    student=student,
                    course=course,
                    WeekNumber='Week - ' + str(week_number),
                    PercentileGrade=grade_info['current_score'],
                    AlphabetGrade=grade_info['current_grade'],
                    categorized_assignment_grades = category_percentages_json
                )

                return JsonResponse({"success": True, "message": "Grade information updated successfully."})
                
        return JsonResponse({"success": False, "message": "Student enrollment not found."})
    else:
        return JsonResponse({"success": False, "message": "Failed to fetch enrollment information."})
    


def sync_canvas_data():
    from .utils import calculate_score_and_letter_grade
    api_url = "https://colostate.instructure.com/api/v1/"
    headers = {
        "Authorization": "Bearer 3716~eFecnK3f2cDrkawtPCRPvVJCLvNDUE2yZZDkKZDWEv4uH36vrzCEeJf4T4QrhNQW"
    }

    # Fetch all courses
    course_response = requests.get(f"{api_url}courses", headers=headers)
    if course_response.status_code != 200:
        print("Failed to fetch courses")
        return

    courses = course_response.json()
    for course in courses:
        course_id = course['id']
        course_name = course['name']
        course_code = course.get('course_code', '')

        # --- Fetch and save instructor name ---
        instructor_name = "N/A"
        teacher_url = f"{api_url}courses/{course_id}/enrollments?type[]=TeacherEnrollment&per_page=1"
        teacher_res = requests.get(teacher_url, headers=headers)
        if teacher_res.status_code == 200:
            teacher_data = teacher_res.json()
            if teacher_data:
                instructor_name = teacher_data[0]['user'].get('sortable_name') or teacher_data[0]['user'].get('name')

        course_obj, _ = Course.objects.update_or_create(
            course_id=course_id,
            defaults={
                'course_name': course_name,
                'course_code': course_code,
                'instructor': instructor_name
            }
        )

        # --- Enrollments ---
        enrollments_resp = requests.get(f"{api_url}courses/{course_id}/enrollments", headers=headers)
        if enrollments_resp.status_code != 200:
            continue

        enrollments_data = enrollments_resp.json()
        for enrollment in enrollments_data:
            user = enrollment['user']
            user_id = user['id']
            user_name = user['name']
            role = enrollment['type']

            user_obj, _ = Student.objects.update_or_create(
                student_id=user_id,
                defaults={'student_name': user_name}
            )

            current_score = None
            current_grade = None

            if role == "StudentEnrollment":
                grade_resp = requests.get(f"{api_url}users/{user_id}/enrollments?type[]=StudentEnrollment", headers=headers)
                if grade_resp.status_code == 200:
                    for enr in grade_resp.json():
                        if enr['course_id'] == course_id:
                            grades = enr.get('grades', {})
                            current_score = grades.get('current_score')
                            current_grade = grades.get('current_grade')
                            print(f"🎯 Grade for {user_name}: {current_score}% ({current_grade})")
                            break

            Enrollment.objects.update_or_create(
                student=user_obj,
                course=course_obj,
                role=role,
                defaults={
                    'current_score': current_score,
                    'current_grade': current_grade
                }
            )

        # --- Assignment Groups ---
        group_resp = requests.get(f"{api_url}courses/{course_id}/assignment_groups", headers=headers)
        if group_resp.status_code == 200:
            for group in group_resp.json():
                group_id = group['id']
                AssignmentGroup.objects.update_or_create(
                    group_id=group_id,
                    defaults={
                        'name': group['name'],
                        'course': course_obj,
                        'group_weight': group.get('group_weight', 0.0)
                    }
                )

        # --- Assignments ---
        assignment_resp = requests.get(f"{api_url}courses/{course_id}/assignments", headers=headers)
        if assignment_resp.status_code == 200:
            for assignment in assignment_resp.json():
                assignment_id = assignment['id']
                group_id = assignment.get('assignment_group_id')
                group = AssignmentGroup.objects.filter(group_id=group_id).first()
                points = assignment.get('points_possible', 0)

                assignment_obj, _ = Assignment.objects.update_or_create(
                    assignment_id=assignment_id,
                    defaults={
                        'name': assignment['name'],
                        'course': course_obj,
                        'assignment_group': group,
                        'points_possible': points
                    }
                )

                sub_resp = requests.get(f"{api_url}courses/{course_id}/assignments/{assignment_id}/submissions", headers=headers)
                if sub_resp.status_code == 200:
                    for sub in sub_resp.json():
                        student = Student.objects.filter(student_id=sub['user_id']).first()
                        if student:
                            Grade.objects.update_or_create(
                                student=student,
                                assignment=assignment_obj,
                                defaults={'score': sub.get('score')}
                            )

    # --- WeeklyGrade Update ---
    for course in Course.objects.all():
        for student in Student.objects.all():
            if not course.enrollment_set.filter(student=student, role='StudentEnrollment').exists():
                continue

            enrollment = Enrollment.objects.filter(student=student, course=course, role='StudentEnrollment').first()
            if not enrollment or enrollment.current_score is None or enrollment.current_grade is None:
               print(f"⚠️ Skipping WeeklyGrade for {student.student_name} in {course.course_name} — grade info missing")
               continue

            WeeklyGrade.objects.filter(
                student=student,
                course=course,
                WeekNumber='Week - 6'
            ).delete()

            WeeklyGrade.objects.create(
            student=student,
            course=course,
            WeekNumber='Week - 6',
            PercentileGrade=enrollment.current_score,
            AlphabetGrade=enrollment.current_grade,
            categorized_assignment_grades='{}'
            )


from dateutil.parser import parse  # ✅ Correct import
def sync_cs152_data(request):
    TOKEN = "3716~eFecnK3f2cDrkawtPCRPvVJCLvNDUE2yZZDkKZDWEv4uH36vrzCEeJf4T4QrhNQW"  # 🔁 Replace with actual token
    COURSE_ID = 186019 # CS152 course ID
    BASE_URL = "https://colostate.instructure.com/api/v1"
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # --- 1. Get course info ---
    course_url = f"{BASE_URL}/courses/{COURSE_ID}"
    course_res = requests.get(course_url, headers=headers)
    if course_res.status_code != 200:
        return HttpResponse("❌ Failed to fetch course info.")

    course_data = course_res.json()

    # --- 2. Get instructor name ---
    instructor_name = "N/A"
    teacher_url = f"{BASE_URL}/courses/{COURSE_ID}/enrollments?type[]=TeacherEnrollment&per_page=1"
    teacher_res = requests.get(teacher_url, headers=headers)
    if teacher_res.status_code == 200:
        teacher_data = teacher_res.json()
        if teacher_data:
            instructor_name = teacher_data[0]['user'].get('sortable_name') or teacher_data[0]['user'].get('name')

    # --- 3. Save course ---
    start_at = course_data.get("start_at")
    end_at = course_data.get("end_at")
    start_date = parse(start_at) if start_at else None
    end_date = parse(end_at) if end_at else None

    course, _ = Course.objects.update_or_create(
        course_id=course_data['id'],
        defaults={
            "course_name": course_data['name'],
            "course_code": course_data.get('course_code', ''),
            "instructor": instructor_name,
            "term": course_data.get('term', {}).get('name', ''),
            "start_date": start_date,
            "end_date": end_date
        }
    )

    # --- 4. Get assignment groups ---
    group_url = f"{BASE_URL}/courses/{COURSE_ID}/assignment_groups?include=assignments"
    group_res = requests.get(group_url, headers=headers)
    if group_res.status_code != 200:
        return HttpResponse("❌ Failed to fetch assignment groups.")

    AssignmentGroup.objects.filter(course=course).delete()
    group_data = group_res.json()

    for group in group_data:
        ag = AssignmentGroup.objects.create(
            group_id=group['id'],
            name=group['name'],
            group_weight=group.get('group_weight', 0),
            course=course
        )
        for a in group.get("assignments", []):
            due_str = a.get('due_at')
            due_at = parse(due_str) if due_str else None

            Assignment.objects.update_or_create(
                assignment_id=a['id'],
                defaults={
                    'name': a['name'],
                    'points_possible': a.get('points_possible'),
                    'assignment_group': ag,
                    'course': course,
                    'due_at': due_at
                }
            )

    # --- 5. Paginated fetch for all enrollments ---
    enrollments = []
    enroll_url = f"{BASE_URL}/courses/{COURSE_ID}/enrollments?type[]=StudentEnrollment&per_page=100"
    
    while enroll_url:
        enroll_res = requests.get(enroll_url, headers=headers)
        if enroll_res.status_code != 200:
            return HttpResponse("❌ Failed during enrollment fetch.")

        enrollments.extend(enroll_res.json())
        enroll_url = enroll_res.links.get("next", {}).get("url")

    Enrollment.objects.filter(course=course, role="StudentEnrollment").delete()

    for e in enrollments:
        user = e['user']
        student, _ = Student.objects.get_or_create(
            student_id=str(user['id']),
            defaults={"student_name": user.get("sortable_name", user["name"])}
        )
        Enrollment.objects.update_or_create(
            student=student,
            course=course,
            role="StudentEnrollment",
            defaults={
                "current_score": e.get('grades', {}).get('current_score'),
                "current_grade": e.get('grades', {}).get('current_grade')
            }
        )

    # --- 6. Get submissions + grades ---
    for enrollment in Enrollment.objects.filter(course=course):
        student = enrollment.student
        sub_url = f"{BASE_URL}/courses/{COURSE_ID}/students/submissions?student_ids[]={student.student_id}&per_page=100"
        sub_res = requests.get(sub_url, headers=headers)
        if sub_res.status_code != 200:
            continue

        submissions = sub_res.json()
        Grade.objects.filter(student=student, assignment__course=course).delete()

        for sub in submissions:
            assignment_id = sub['assignment_id']
            try:
                assignment = Assignment.objects.get(assignment_id=assignment_id)
                Grade.objects.create(
                    student=student,
                    assignment=assignment,
                    score=sub.get('score', 0)
                )
            except Assignment.DoesNotExist:
                continue

    return HttpResponse("✅ CS152 data synced with full student enrollment (pagination-safe).")

def test_canvas_course_access(request):
    TOKEN = "3716~eFecnK3f2cDrkawtPCRPvVJCLvNDUE2yZZDkKZDWEv4uH36vrzCEeJf4T4QrhNQW"  # Professor token
    COURSE_ID = 186019
    BASE_URL = "https://colostate.instructure.com/api/v1"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    url = f"{BASE_URL}/courses/{COURSE_ID}/enrollments?type[]=StudentEnrollment&per_page=100"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        enrollments = response.json()
        simplified = []
        for e in enrollments:
            simplified.append({
                "student_id": e["user"]["id"],
                "student_name": e["user"]["sortable_name"],
                "grades": e.get("grades")
            })
        return JsonResponse(simplified, safe=False)
    else:
        return JsonResponse({"error": "Failed to fetch enrollments", "status_code": response.status_code})



from collections import defaultdict
from datetime import timedelta

def extract_student_features_by_group_name(student_id, course_id, progress_ratio):
    course = Course.objects.get(course_id=course_id)
    duration = (course.end_date - course.start_date).days
    cutoff = course.start_date + timedelta(days=int(duration * progress_ratio))

    assignment_groups = AssignmentGroup.objects.filter(course=course)
    group_id_to_name = {g.group_id: g.name for g in assignment_groups}

    assignments = Assignment.objects.filter(course=course, due_at__lte=cutoff)
    grades = Grade.objects.filter(student__student_id=student_id, assignment_id__in=assignments.values_list('assignment_id', flat=True))

    features = defaultdict(float)
    totals = defaultdict(float)

    for grade in grades:
        if not grade.assignment.assignment_group:
            continue
        group_id = grade.assignment.assignment_group.group_id
        group_name = group_id_to_name.get(group_id)
        if group_name and grade.assignment.points_possible:
            features[group_name] += grade.score or 0
            totals[group_name] += grade.assignment.points_possible

    final_features = {}
    for group_name in features:
        total_possible = totals[group_name]
        final_features[group_name] = (features[group_name] / total_possible) if total_possible > 0 else 0

    return final_features


def sync_view(request):
    sync_canvas_data()  # this calls the function that fetches from Canvas and stores in your DB
    return HttpResponse("✅ Sync complete. Data saved to database.")

# def list_view(request):

#     student = Student(student_id='8120830', student_name='Rakshith Kumar')
#     student.save()

#     items = Student.objects.all()
#     for item in items:
#         print(f"ID: {item.student_id}, Name: {item.student_name}")
#     # return render(request, 'myapp/template_list.html', {'items': items})

