from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="principal_dashboard"),
    path("manage-users/", views.manage_users, name="principal_manage_users"),
    path("assign-teacher/", views.assign_teacher, name="principal_assign_teacher"),
    path(
        "delete-student/<int:student_id>/",
        views.delete_student,
        name="principal_delete_student",
    ),
    path(
        "delete-teacher/<int:teacher_id>/",
        views.delete_teacher,
        name="principal_delete_teacher",
    ),
]
