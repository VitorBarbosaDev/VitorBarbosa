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
    featured_posts = BlogPost.objects.filter(is_live=True, featured=True)
    if featured_posts.exists():
        blog_posts = featured_posts[:3]
    else:
        blog_posts = BlogPost.objects.filter(is_live=True)[:3]
    return render(request, 'projects/home.html', {
        'profile': profile,
        'projects': projects,
        'cv': cv,
        'blog_posts': blog_posts,
    })

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

def project_detail(request, slug):
    project = Project.objects.filter(slug=slug).first()
    if not project:
        # Support legacy integer PK URLs with permanent redirect to slug URL
        if slug.isdigit():
            project = get_object_or_404(Project, pk=int(slug))
            return redirect('project_detail', slug=project.slug, permanent=True)
        get_object_or_404(Project, slug=slug)

    blog_posts = BlogPost.objects.filter(projects=project, is_live=True)
    template = f"projects/project_detail_{project.template}.html"
    return render(request, template, {'project': project, 'blog_posts': blog_posts})


def blog_list(request):
    posts = BlogPost.objects.filter(is_live=True)
    active_project = None
    project_identifier = request.GET.get('project')
    if project_identifier:
        if project_identifier.isdigit():
            active_project = Project.objects.filter(pk=int(project_identifier)).first()
            if not active_project:
                active_project = get_object_or_404(Project, slug=project_identifier)
        else:
            active_project = get_object_or_404(Project, slug=project_identifier)
        posts = posts.filter(projects=active_project)

    # Show untagged posts only
    show_untagged = request.GET.get('untagged')
    if show_untagged:
        posts = posts.filter(projects__isnull=True)

    # Sorting
    sort = request.GET.get('sort')
    if sort == 'views':
        posts = posts.order_by('-views', '-created_on')
    else:
        # Default is already -created_on in Meta, but we can be explicit
        posts = posts.order_by('-created_on')

    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Projects that have at least one live blog post
    tagged_projects = Project.objects.filter(blog_posts__is_live=True).distinct()

    # Split into featured projects (shown as individual buttons) and other projects (in dropdown)
    if tagged_projects.filter(featured=True).exists():
        featured_projects = list(tagged_projects.filter(featured=True))
        other_projects = list(tagged_projects.filter(featured=False))
    else:
        if tagged_projects.count() <= 4:
            featured_projects = list(tagged_projects)
            other_projects = []
        else:
            featured_projects = list(tagged_projects[:3])
            other_projects = list(tagged_projects[3:])

    is_active_in_other = active_project is not None and any(p.pk == active_project.pk for p in other_projects)

    return render(request, 'projects/blog_list.html', {
        'page_obj': page_obj,
        'active_project': active_project,
        'tagged_projects': tagged_projects,
        'featured_projects': featured_projects,
        'other_projects': other_projects,
        'is_active_in_other': is_active_in_other,
        'show_untagged': show_untagged,
        'current_sort': sort,
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

