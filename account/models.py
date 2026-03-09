from django.db import models
from django.contrib.auth.models import User
from academics.models import SchoolClass


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=50)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50)

    def __str__(self):
        return self.user.username


class TeacherClassSubject(models.Model):
    teacher = models.ForeignKey("account.TeacherProfile", on_delete=models.CASCADE)
    school_class = models.ForeignKey("academics.SchoolClass", on_delete=models.CASCADE)
    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("teacher", "school_class", "subject")
