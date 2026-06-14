from django.urls import path
from . import views

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("<int:course_id>/", views.course_detail, name="course_detail"),
    path("lessons/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("lessons/<int:lesson_id>/test/", views.test_detail, name="test_detail"),
    path("lessons/<int:lesson_id>/submit/", views.test_submit, name="test_submit"),
    path(
        "lesson/<int:lesson_id>/complete/",
        views.complete_lesson,
        name="complete_lesson",
    ),  # ← ДОБАВИТЬ
    path("task/<int:task_id>/", views.task_detail, name="task_detail"),
    path("run-code/", views.run_code, name="run_code"),
    path("check-task/<int:task_id>/", views.check_task, name="check_task"),
]
