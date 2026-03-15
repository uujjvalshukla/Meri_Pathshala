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
    # =========  This is For Show Teacher List and Student List = ===========
    path("students/", views.student_list, name="principal_student_list"),
    path("students/<int:student_id>/", views.student_detail, name="principal_student_detail"),
    path("teachers/", views.teacher_list, name="principal_teacher_list"),
    path("teachers/<int:teacher_id>/", views.teacher_detail, name="principal_teacher_detail"),
    path("assignments/", views.assignment_list, name="principal_assignment_list"),
    path("assignments/<int:assignment_id>/", views.assignment_detail, name="principal_assignment_detail"),
]

