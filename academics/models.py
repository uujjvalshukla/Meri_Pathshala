from django.db import models


class SchoolClass(models.Model):
    name = models.CharField(max_length=10, unique=True)  # 5,6,7,...12

    def __str__(self):
        return f"Class {self.name}"


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Hindi,English,Math,...

    def __str__(self):
        return self.name
