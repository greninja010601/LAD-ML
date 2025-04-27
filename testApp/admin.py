from django.contrib import admin
from .models import Course

# Register your models here.
from .models import Enrollment
admin.site.register(Enrollment)

class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_id', 'course_name', 'term', 'instructor']