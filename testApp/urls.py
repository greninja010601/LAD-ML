from . import views
from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

urlpatterns=[
path('',views.index,name='index'),
path('screen_1/<int:course_id>/<str:course_name>/<str:student_name>/<str:user_id>/', views.screen_1, name='screen_1'),
path('screen_2/', views.screen_2, name='screen_2'),
path('screen_3/', views.screen_3, name='screen_3'),
path('screen_4/', views.screen_4, name='screen_4'),
path('screen_5/<str:term>/', views.screen_5, name='screen_5'),
path('screen_6/<int:course_id>/', views.screen_6, name='screen_6'),
path('screen_7/<int:course_id>/<str:course_name>/<str:student_name>/<str:user_id>/', views.screen_7, name='screen_7'),
path('screen_8/<int:course_id>/<str:course_name>/<str:student_name>/<str:user_id>/', views.screen_8, name='screen_8'),
path('screen_9/<int:course_id>/<str:course_name>/<str:student_name>/<str:user_id>/', views.screen_9, name='screen_9'),
path('screen_10/<int:course_id>/<int:student_id>/', views.screen_10, name='screen_10'),
path('calendar/', views.calendar_view, name='calendar_view'),
path('', views.update_student_grades, name='update_student_grades'),
path('test-token/', views.test_token),
path('test_cs152/', views.test_canvas_course_access, name='test_cs152'),
path('sync_cs152/', views.sync_cs152_data, name='sync_cs152'),
path('sync-canvas/', views.sync_view, name='sync-canvas'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)