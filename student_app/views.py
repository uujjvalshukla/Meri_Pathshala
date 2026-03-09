from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from account.models import StudentProfile
from assignments.models import Assignment, Submission
from django.http import JsonResponse, HttpResponse
from sympy import *
import re
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from sympy import sin, cos, tan, asin, acos, atan, log, exp, sqrt, pi, E
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

# ----------  Student Dashboard -------------------------


@login_required
def dashboard(request):

    # ❗ Explicit role check (beginner friendly)
    if not hasattr(request.user, "studentprofile"):
        return HttpResponse("Access denied. Student only.")

    student = request.user.studentprofile

    assignments = Assignment.objects.filter(
        school_class=student.school_class
    ).select_related("subject")

    rows = []

    for assignment in assignments:

        submission = Submission.objects.filter(
            assignment=assignment,
            student=student,
        ).first()

        rows.append(
            {
                "assignment": assignment,
                "submission": submission,
            }
        )

    return render(
        request,
        "student/dashboard.html",
        {
            "student": student,
            "rows": rows,
        },
    )


#   ------------------     2️⃣ Assignment Detail + Submit   --------------------------


@login_required
def assignment_detail(request, assignment_id):

    if not hasattr(request.user, "studentprofile"):
        return HttpResponse("Access denied. Student only.")

    student = request.user.studentprofile

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        school_class=student.school_class,  # 🔐 safety check
    )

    # Existing submission (if any)
    existing_submission = Submission.objects.filter(
        assignment=assignment,
        student=student,
    ).first()

    # 🔒 HARD LOCK: if teacher has checked, student cannot edit
    if existing_submission and (
        existing_submission.marks is not None or existing_submission.feedback
    ):
        return render(
            request,
            "student/assignment_detail.html",
            {
                "assignment": assignment,
                "submission": existing_submission,
                "locked": True,
            },
        )

    # =====================
    # Save / Update submission
    # =====================
    if request.method == "POST":

        answer_text = request.POST.get("answer_text")
        file = request.FILES.get("file")

        Submission.objects.update_or_create(
            assignment=assignment,
            student=student,
            defaults={
                "answer_text": answer_text,
                "file": file,
            },
        )

        return redirect("student_dashboard")

    return render(
        request,
        "student/assignment_detail.html",
        {
            "assignment": assignment,
            "submission": existing_submission,
            "locked": False,
        },
    )


# ==========================================================
#   Add Scientific Calculator
# ============================================================


# --- helpers ---
_transformations = standard_transformations + (
    implicit_multiplication_application,  # allows 2pi, 2(3+4), etc.
    convert_xor,  # converts ^ to **
)

_ALLOWED = {
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "asin": asin,
    "acos": acos,
    "atan": atan,
    "log": log,
    "ln": log,  # treat ln as log
    "exp": exp,
    "sqrt": sqrt,
    "pi": pi,
    "E": E,
    "e": E,
}

# only allow these characters (keeps input sane)
_ALLOWED_CHARS_RE = re.compile(r"^[0-9+\-*/().,^ \tA-Za-z_]+$")


def _to_radians_if_needed(expr_str: str, mode: str) -> str:
    """
    Convert trig args to radians when mode=DEG:
    sin(x) => sin(pi*x/180)
    cos(30) => cos(pi*30/180)
    Works for sin/cos/tan and their inverse too (we convert input for inverse trig as well).
    """
    if mode != "DEG":
        return expr_str

    # wrap argument inside trig calls: func(arg) -> func(pi*(arg)/180)
    # this is still string-based, but safer than your earlier approach because it wraps properly.
    trig_funcs = ["sin", "cos", "tan", "asin", "acos", "atan"]
    for f in trig_funcs:
        expr_str = re.sub(rf"{f}\s*\(", f"{f}(pi*(", expr_str)
    # close the inserted "(pi*(" with ")/180)" for each trig call.
    # We do this by replacing every closing ')' with ')/180)' ONLY for trig calls is hard without full parsing.
    # Practical compromise: do not auto-close. Instead, we do a simpler but correct transformation using parse tree below.
    return expr_str  # We'll do a better conversion below with AST


def _convert_trig_args_ast(expr, mode: str):
    """
    AST-level conversion (correct):
    sin(x) in DEG => sin(pi*x/180)
    """
    if mode != "DEG":
        return expr

    from sympy import Function
    from sympy.core.function import AppliedUndef

    trig_set = {sin, cos, tan, asin, acos, atan}

    def _recurse(e):
        # If it's a trig function call: f(arg)
        if hasattr(e, "func") and e.func in trig_set and len(e.args) == 1:
            arg = _recurse(e.args[0])
            return e.func(pi * arg / 180)
        # Generic recursion
        if hasattr(e, "args") and e.args:
            return e.func(*[_recurse(a) for a in e.args])
        return e

    return _recurse(expr)


# Allow: numbers, operators, parentheses, dot, commas, spaces, letters (functions)
_ALLOWED_CHARS_RE = re.compile(r"^[0-9+\-*/().,^ \tA-Za-z_,]+$")

_TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,  # 2pi, 2(3+4)
    convert_xor,  # ^ -> **
)


# Define "real calculator" meanings:
def LOG10(x):
    return log(x, 10)  # base-10 log


def LN(x):
    return log(x)  # natural log


_ALLOWED_FUNCS = {
    # trig
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "asin": asin,
    "acos": acos,
    "atan": atan,
    # logs
    "log": LOG10,  # IMPORTANT: log() = log10()
    "ln": LN,  # ln() = natural log
    # misc
    "sqrt": sqrt,
    "exp": exp,
    "pi": pi,
    "E": E,
    "e": E,
}

_TRIG_DIRECT = {sin, cos, tan}
_TRIG_INVERSE = {asin, acos, atan}


def _convert_deg_rad(expr, mode: str):
    """
    DEG mode:
      sin(x) -> sin(pi*x/180)
      cos(x) -> cos(pi*x/180)
      tan(x) -> tan(pi*x/180)

      asin(x) -> asin(x) * 180/pi
      acos(x) -> acos(x) * 180/pi
      atan(x) -> atan(x) * 180/pi
    """
    if mode != "DEG":
        return expr

    def walk(e):
        # trig direct: convert input degrees to radians
        if hasattr(e, "func") and e.func in _TRIG_DIRECT and len(e.args) == 1:
            arg = walk(e.args[0])
            return e.func(pi * arg / 180)

        # inverse trig: convert output radians to degrees
        if hasattr(e, "func") and e.func in _TRIG_INVERSE and len(e.args) == 1:
            arg = walk(e.args[0])
            return e.func(arg) * 180 / pi

        # generic recursion
        if hasattr(e, "args") and e.args:
            return e.func(*[walk(a) for a in e.args])
        return e

    return walk(expr)


@login_required
def evaluate_expression(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid Request"}, status=400)

    if not hasattr(request.user, "studentprofile"):
        return JsonResponse({"error": "Access denied. Student only."}, status=403)

    expression = (request.POST.get("expression") or "").strip()
    mode = (request.POST.get("mode") or "RAD").upper()

    if not expression:
        return JsonResponse({"error": "Empty expression"}, status=400)

    # basic protection
    if len(expression) > 200:
        return JsonResponse({"error": "Expression too long"}, status=400)

    if not _ALLOWED_CHARS_RE.match(expression):
        return JsonResponse({"error": "Invalid characters"}, status=400)

    try:
        # Parse with whitelist only (safer than raw sympify)
        expr = parse_expr(
            expression,
            local_dict=_ALLOWED_FUNCS,
            transformations=_TRANSFORMS,
            evaluate=True,
        )

        # DEG/RAD adjustments
        expr = _convert_deg_rad(expr, mode)

        # Numeric result like a real calculator
        result = expr.evalf(12)  # 12-digit precision
        return JsonResponse({"result": str(result)})

    except Exception:
        return JsonResponse({"error": "Invalid Expression"}, status=400)


@login_required
def calculator_page(request):
    if not hasattr(request.user, "studentprofile"):
        return HttpResponse("Access denied. Student only.", status=403)
    return render(request, "student/calculator.html")
