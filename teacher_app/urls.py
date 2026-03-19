from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="teacher_dashboard"),
    path(
        "create-assignment/", views.create_assignment, name="teacher_create_assignment"
    ),
    path(
        "submissions/<int:assignment_id>/",
        views.assignment_submissions,
        name="assignment_submissions",
    ),
    path("ai-generate/", views.generate_ai_assignment, name="teacher_ai_generate"),
    path(
        "submission/<int:submission_id>/",
        views.submission_detail,
        name="teacher_submission_detail",
    ),
    path(
        "assignment/<int:assignment_id>/",
        views.assignment_detail,
        name="teacher_assignment_detail",
    ),
]
