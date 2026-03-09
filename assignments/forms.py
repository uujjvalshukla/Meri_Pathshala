from django import forms
from .models import Assignment


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = [
            "title",
            "description",
            "school_class",
            "subject",
            "due_date",
            "total_marks",
        ]
