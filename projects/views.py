from django.shortcuts import render
from .models import Project, CV

def home(request):
    projects = Project.objects.all()
    cv = CV.objects.first()
    return render(request, 'projects/home.html', {'projects': projects, 'cv': cv})
