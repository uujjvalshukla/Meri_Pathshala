from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="student_dashboard"),
    path(
        "assignment/<int:assignment_id>/",
        views.assignment_detail,
        name="student_assignment_detail",
    ),
    path("calculator/", views.calculator_page, name="calculator"),
    # AJAX endpoint
    path("calculate/", views.evaluate_expression, name="calculate"),
]
