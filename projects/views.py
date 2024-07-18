from django.shortcuts import render, get_object_or_404
from .models import Project, Profile, CV

def home(request):
    profile = Profile.objects.first()
    projects = Project.objects.filter(featured=True)
    cv = CV.objects.first()
    return render(request, 'projects/home.html', {'profile': profile, 'projects': projects, 'cv': cv})

def about(request):
    profile = Profile.objects.first()
    cv = CV.objects.first()
    return render(request, 'projects/about.html', {'profile': profile, 'cv': cv})

def full_stack(request):
    projects = Project.objects.filter(category='Full Stack')
    return render(request, 'projects/full_stack.html', {'projects': projects})

def games(request):
    projects = Project.objects.filter(category='Games')
    return render(request, 'projects/games.html', {'projects': projects})

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    template = f"projects/project_detail_{project.template}.html"
    return render(request, template, {'project': project})
