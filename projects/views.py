from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Project, Profile, CV, BlogPost

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
    blog_posts = BlogPost.objects.filter(projects=project)
    template = f"projects/project_detail_{project.template}.html"
    return render(request, template, {'project': project, 'blog_posts': blog_posts})


def blog_list(request):
    posts = BlogPost.objects.all()
    active_project = None
    project_pk = request.GET.get('project')
    if project_pk:
        active_project = get_object_or_404(Project, pk=project_pk)
        posts = posts.filter(projects=active_project)

    # Show untagged posts only
    show_untagged = request.GET.get('untagged')
    if show_untagged:
        posts = posts.filter(projects__isnull=True)

    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Projects that have at least one blog post (for filter dropdown)
    tagged_projects = Project.objects.filter(blog_posts__isnull=False).distinct()

    return render(request, 'projects/blog_list.html', {
        'page_obj': page_obj,
        'active_project': active_project,
        'tagged_projects': tagged_projects,
        'show_untagged': show_untagged,
    })


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    return render(request, 'projects/blog_detail.html', {'post': post})
