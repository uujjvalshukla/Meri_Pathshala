from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages


# =========================  Login Page View =================================


def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:
            return render(
                request,
                "auth/login.html",
                {"error": "Invalid username or password"},
            )

        login(request, user)
        messages.success(request, "Login successful")

        # ===== ROLE-BASED REDIRECT (CLEAR + SIMPLE) =====

        # PRINCIPAL
        if user.groups.filter(name="Principal").exists():
            return redirect("principal_dashboard")

        # TEACHER
        if hasattr(user, "teacherprofile"):
            return redirect("teacher_dashboard")

        # STUDENT
        if hasattr(user, "studentprofile"):
            return redirect("student_dashboard")

        # SAFETY FALLBACK
        logout(request)
        return HttpResponse("You are not assigned to any role.")

    return render(request, "auth/login.html")


#  -----------------   logout Function -----------------------


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")
