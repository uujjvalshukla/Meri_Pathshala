from django.db import models


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    school_class = models.ForeignKey("academics.SchoolClass", on_delete=models.CASCADE)
    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE)
    teacher = models.ForeignKey("account.TeacherProfile", on_delete=models.CASCADE)
    due_date = models.DateField()
    total_marks = models.IntegerField(default=10) 

    def __str__(self):
        return self.title


class Submission(models.Model):
    assignment = models.ForeignKey("assignments.Assignment", on_delete=models.CASCADE)
    student = models.ForeignKey("account.StudentProfile", on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True)
    file = models.FileField(upload_to="submissions/", blank=True, null=True)

    extracted_text = models.TextField(blank=True)  # New Extracted text

    submitted_at = models.DateTimeField(auto_now_add=True)
    marks = models.IntegerField(blank=True, null=True)
    feedback = models.TextField(blank=True)
    ai_marks = models.IntegerField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)
    is_checked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("assignment", "student")

    def __str__(self):
        return f"{self.student} - {self.assignment.title}"

    def is_checked(self):
        return self.marks is not None or bool(self.feedback)
