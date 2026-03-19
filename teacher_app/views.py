from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse

from account.models import TeacherProfile, TeacherClassSubject
from assignments.forms import AssignmentForm
from assignments.models import Assignment, Submission
from ai.services import generate_assignment, process_and_evaluate_submission


@login_required
def dashboard(request):

    #   role check
    if not hasattr(request.user, "teacherprofile"):
        return HttpResponse("Access denied. Teacher only.")

    teacher = request.user.teacherprofile

    teaching = TeacherClassSubject.objects.filter(teacher=teacher).select_related(
        "school_class", "subject"
    )

    assignments = Assignment.objects.filter(teacher=teacher).select_related(
        "school_class", "subject"
    )

    return render(
        request,
        "teacher/dashboard.html",
        {
            "teaching": teaching,
            "assignments": assignments,
        },
    )


# ------------------------------2️⃣ Create Assignment      --------------------------------


@login_required
def create_assignment(request):

    if not hasattr(request.user, "teacherprofile"):
        return HttpResponse("Access denied. Teacher only.")

    teacher = request.user.teacherprofile

    if request.method == "POST":
        form = AssignmentForm(request.POST)

        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = teacher
            assignment.save()

            return redirect("teacher_dashboard")

    else:
        form = AssignmentForm()

    return render(
        request,
        "teacher/create_assignment.html",
        {"form": form},
    )


# ---------------  Generate Assignment with AI -----------------


@login_required
def generate_ai_assignment(request):

    # ==============    role check   =========
    if not hasattr(request.user, "teacherprofile"):
        return JsonResponse({"error": "Teacher only"}, status=403)

    if request.method == "POST":
        board = request.POST.get("board")
        class_name = request.POST.get("class_name")
        chapter = request.POST.get("chapter")
        num_questions = request.POST.get("num_questions")
        subject = request.POST.get("subject", "")
        difficulty = request.POST.get("difficulty", "Medium")

        text = generate_assignment(
            board=board,
            class_name=class_name,
            chapter=chapter,
            num_questions=num_questions,
            subject=subject,
            difficulty=difficulty,
        )

        return JsonResponse({"assignment": text})

    return JsonResponse({"error": "Invalid request"}, status=400)


# --------------------------3️⃣ View Assignment Submissions  ------------------------


@login_required
def assignment_submissions(request, assignment_id):

    if not hasattr(request.user, "teacherprofile"):
        return HttpResponse("Access denied. Teacher only.")

    teacher = request.user.teacherprofile

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        teacher=teacher,  # =========    Ownership check     ===============
    )

    submissions = Submission.objects.filter(assignment=assignment).select_related(
        "student__user"
    )

    return render(
        request,
        "teacher/assignment_submissions.html",
        {
            "assignment": assignment,
            "submissions": submissions,
        },
    )


# ---------------     4️⃣ Submission Detail + AI Evaluation   ----------------------------


@login_required
def submission_detail(request, submission_id):

    if not hasattr(request.user, "teacherprofile"):
        return HttpResponse("Access denied. Teacher only.")

    teacher = request.user.teacherprofile

    submission = get_object_or_404(
        Submission.objects.select_related("student__user", "assignment"),
        id=submission_id,
        assignment__teacher=teacher,
    )

    assignment_text = submission.assignment.description

    # AI Evaluation ONLY when teacher clicks AI button (?ai=1)
    # ===============================
    # AI Evaluation (Suggestion Only)
    # ===============================
    if request.method == "GET" and request.GET.get("ai") == "1":
        file_path = submission.file.path if submission.file else None

        ai_data = process_and_evaluate_submission(
            assignment_text=assignment_text,
            student_answer_text=submission.answer_text,
            uploaded_file_path=file_path,
            max_marks=submission.assignment.total_marks,
        )

        ai_result = ai_data["evaluation"]

        # Extract readable text (save only this if needed)
        if ai_data.get("extracted_text"):
            submission.extracted_text = ai_data["extracted_text"]
            submission.save()

        try:
            # -------------------------
            # Extract Marks
            # -------------------------
            marks_line = None
            for line in ai_result.splitlines():
                if line.lower().startswith("marks:"):
                    marks_line = line
                    break

            if marks_line:
                marks_value = marks_line.split(":", 1)[1].strip()
                obtained_marks = marks_value.split("/")[0]
                ai_marks = int(obtained_marks)
            else:
                ai_marks = None

            # -------------------------
            # Extract Full Feedback Block
            # -------------------------
            feedback_index = ai_result.lower().find("feedback:")

            if feedback_index != -1:
                ai_feedback = ai_result[feedback_index + len("feedback:") :].strip()
            else:
                ai_feedback = ai_result.strip()

        except Exception:
            ai_marks = None
            ai_feedback = ai_result.strip()

        #  ======    Do NOT save to DB  ===============
        return render(
            request,
            "teacher/submission_detail.html",
            {
                "submission": submission,
                "ai_marks_suggestion": ai_marks,
                "ai_feedback_suggestion": ai_feedback,
            },
        )

    #  Manual Save by Teacher
    if request.method == "POST":
        submission.marks = request.POST.get("marks") or None
        submission.feedback = request.POST.get("feedback")
        submission.save()

        return redirect("teacher_submission_detail", submission_id=submission.id)

    return render(
        request,
        "teacher/submission_detail.html",
        {
            "submission": submission,
            "ai_marks_suggestion": None,
            "ai_feedback_suggestion": None,
        },
    )


# Teacher can view our assignments


@login_required
def assignment_detail(request, assignment_id):

    if not hasattr(request.user, "teacherprofile"):
        return HttpResponse("Access denied. Teacher only.")

    teacher = request.user.teacherprofile

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        teacher=teacher,  # ownership check
    )

    submission_count = Submission.objects.filter(assignment=assignment).count()

    return render(
        request,
        "student/assignment_detail.html",  # reusing student template
        {
            "assignment": assignment,
            "submission_count": submission_count,
            "locked": True,  # hides the submit form, shows only the questions
            "submission": None,
            "back_url": "/teacher/dashboard/",
        },
    )
