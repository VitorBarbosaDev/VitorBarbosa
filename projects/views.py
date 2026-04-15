from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import F
from .models import Project, Profile, CV, BlogPost, Subscriber

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
    blog_posts = BlogPost.objects.filter(projects=project, is_live=True)
    template = f"projects/project_detail_{project.template}.html"
    return render(request, template, {'project': project, 'blog_posts': blog_posts})


def blog_list(request):
    posts = BlogPost.objects.filter(is_live=True)
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
    post = get_object_or_404(BlogPost, slug=slug, is_live=True)
    # Increment view count atomically
    BlogPost.objects.filter(pk=post.pk).update(views=F('views') + 1)
    post.refresh_from_db(fields=['views'])
    return render(request, 'projects/blog_detail.html', {'post': post})


def subscribe(request):
    all_projects = Project.objects.all()
    fullstack_projects = all_projects.filter(category='Full Stack')
    game_projects = all_projects.filter(category='Games')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        subscribe_all = request.POST.get('subscribe_all') == 'on'
        selected_projects = request.POST.getlist('projects')

        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'projects/subscribe.html', {
                'fullstack_projects': fullstack_projects,
                'game_projects': game_projects,
            })

        # Create or update subscriber
        subscriber, created = Subscriber.objects.get_or_create(
            email=email,
            defaults={'subscribe_all': subscribe_all, 'is_active': True},
        )
        if not created:
            # Re-activate if previously unsubscribed
            subscriber.is_active = True
            subscriber.subscribe_all = subscribe_all
            subscriber.save()

        # Set project subscriptions
        if not subscribe_all and selected_projects:
            subscriber.projects.set(selected_projects)
        else:
            subscriber.projects.clear()

        if created:
            messages.success(
                request,
                'You have been subscribed! You will receive email '
                'notifications for new blog posts.',
            )
        else:
            messages.success(
                request, 'Your subscription preferences have been updated!',
            )
        return redirect('subscribe')

    return render(request, 'projects/subscribe.html', {
        'fullstack_projects': fullstack_projects,
        'game_projects': game_projects,
    })


def unsubscribe(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    subscriber.is_active = False
    subscriber.save()
    return render(request, 'projects/unsubscribe_confirm.html')


def manage_subscription(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    all_projects = Project.objects.all()
    fullstack_projects = all_projects.filter(category='Full Stack')
    game_projects = all_projects.filter(category='Games')

    if request.method == 'POST':
        subscribe_all = request.POST.get('subscribe_all') == 'on'
        selected_projects = request.POST.getlist('projects')

        subscriber.subscribe_all = subscribe_all
        subscriber.is_active = True
        subscriber.save()

        if not subscribe_all and selected_projects:
            subscriber.projects.set(selected_projects)
        else:
            subscriber.projects.clear()

        messages.success(request, 'Your subscription preferences have been updated!')
        return redirect('manage_subscription', token=subscriber.token)

    return render(request, 'projects/manage_subscription.html', {
        'subscriber': subscriber,
        'fullstack_projects': fullstack_projects,
        'game_projects': game_projects,
    })

