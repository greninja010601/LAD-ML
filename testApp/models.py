from django.db import models

class Course(models.Model):
    course_id = models.BigIntegerField(primary_key=True)  # same as Canvas course ID
    course_name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=100)
    instructor = models.CharField(max_length=255, blank=True, null=True)
    term = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.course_name} ({self.term})"

class Student(models.Model):
    student_id = models.CharField(max_length=100, primary_key=True)  # allows both int and string formats
    student_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.student_name

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # StudentEnrollment, TeacherEnrollment, etc.
    current_score = models.FloatField(null=True, blank=True)
    current_grade = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course', 'role')

class AssignmentGroup(models.Model):
    group_id = models.BigIntegerField(primary_key=True)  # ✅ FIXED
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    group_weight = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.name} - {self.course.course_name if self.course else 'Unknown'}"

class Assignment(models.Model):
    assignment_id = models.BigIntegerField(primary_key=True)  # ✅ FIXED
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    assignment_group = models.ForeignKey(AssignmentGroup, on_delete=models.SET_NULL, null=True)
    points_possible = models.FloatField(null=True, blank=True)  # ✅ allows nulls
    due_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return self.name

class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    score = models.FloatField(null=True, blank=True)

class WeeklyGrade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    WeekNumber = models.CharField(max_length=50)
    PercentileGrade = models.FloatField()
    AlphabetGrade = models.CharField(max_length=5)
    categorized_assignment_grades = models.TextField()  # JSON string of category-wise grade %

    class Meta:
        unique_together = ('student', 'course', 'WeekNumber')
