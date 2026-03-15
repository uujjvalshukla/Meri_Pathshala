from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User, Group

from account.models import StudentProfile, TeacherProfile, TeacherClassSubject
from academics.models import SchoolClass, Subject


@login_required
def dashboard(request):

    # Explicit role check (very clear)
    if not request.user.groups.filter(name="Principal").exists():
        return HttpResponse("Access denied. Principal only.")

    return render(request, "principal/dashboard.html")


#  --------------   Manage Users (Student + Teacher)   ----------------------------


@login_required
def manage_users(request):

    if not request.user.groups.filter(name="Principal").exists():
        return HttpResponse("Access denied. Principal only.")

    if request.method == "POST":
        user_type = request.POST.get("type")

        # -------- CREATE STUDENT --------
        if user_type == "student":

            username = request.POST.get("username")
            password = request.POST.get("password")
            roll_number = request.POST.get("roll_number")
            class_id = request.POST.get("class_id")

            if not User.objects.filter(username=username).exists():

                user = User.objects.create_user(
                    username=username,
                    password=password,
                )

                student_group = Group.objects.get(name="Student")
                user.groups.add(student_group)

                school_class = get_object_or_404(
                    SchoolClass,
                    id=class_id,
                )

                StudentProfile.objects.create(
                    user=user,
                    roll_number=roll_number,
                    school_class=school_class,
                )

        # -------- CREATE TEACHER --------
        elif user_type == "teacher":

            username = request.POST.get("username")
            password = request.POST.get("password")
            employee_id = request.POST.get("employee_id")

            if not User.objects.filter(username=username).exists():

                user = User.objects.create_user(
                    username=username,
                    password=password,
                )

                teacher_group = Group.objects.get(name="Teacher")
                user.groups.add(teacher_group)

                TeacherProfile.objects.create(
                    user=user,
                    employee_id=employee_id,
                )

        return redirect("principal_manage_users")

    classes = SchoolClass.objects.all()
    students = StudentProfile.objects.select_related("user", "school_class")
    teachers = TeacherProfile.objects.select_related("user")

    return render(
        request,
        "principal/manage_users.html",
        {
            "classes": classes,
            "students": students,
            "teachers": teachers,
        },
    )


#   -----------------   Delete Student  ------------------


@login_required
def delete_student(request, student_id):

    if not request.user.groups.filter(name="Principal").exists():
        return HttpResponse("Access denied. Principal only.")

    student = get_object_or_404(
        StudentProfile,
        id=student_id,
    )

    # delete linked auth user
    student.user.delete()

    return redirect("principal_manage_users")


#   ------------------   Delete Teacher   --------------


@login_required
def delete_teacher(request, teacher_id):

    if not request.user.groups.filter(name="Principal").exists():
        return HttpResponse("Access denied. Principal only.")

    teacher = get_object_or_404(
        TeacherProfile,
        id=teacher_id,
    )

    teacher.user.delete()

    return redirect("principal_manage_users")


#    ------------ Assign Teacher to Class + Subject   --------------


@login_required
def assign_teacher(request):

    if not request.user.groups.filter(name="Principal").exists():
        return HttpResponse("Access denied. Principal only.")

    if request.method == "POST":

        teacher_id = request.POST.get("teacher_id")
        class_id = request.POST.get("class_id")
        subject_id = request.POST.get("subject_id")

        TeacherClassSubject.objects.get_or_create(
            teacher_id=teacher_id,
            school_class_id=class_id,
            subject_id=subject_id,
        )

        return redirect("principal_assign_teacher")

    teachers = TeacherProfile.objects.select_related("user")
    classes = SchoolClass.objects.all()
    subjects = Subject.objects.all()

    mappings = TeacherClassSubject.objects.select_related(
        "teacher__user",
        "school_class",
        "subject",
    )

    return render(
        request,
        "principal/assign_teacher.html",
        {
            "teachers": teachers,
            "classes": classes,
            "subjects": subjects,
            "mappings": mappings,
        },
    )
