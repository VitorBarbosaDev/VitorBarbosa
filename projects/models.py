import uuid

from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField

class Project(models.Model):
    CATEGORY_CHOICES = [
        ('Full Stack', 'Full Stack'),
        ('Games', 'Games'),
    ]
    TEMPLATE_CHOICES = [
        ('default', 'Default'),
        ('gallery', 'Gallery'),
        ('feature', 'Feature'),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    image = CloudinaryField('projects/', default='default.jpg')
    additional_images = models.ManyToManyField('ProjectImage', blank=True)
    github_link = models.URLField(blank=True, null=True)  # Make optional
    live_link = models.URLField(blank=True, null=True)
    download_link = models.URLField(blank=True, null=True)  # New field for download link
    external_link = models.URLField(blank=True, null=True)  # New field for external dev page
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='Full Stack')
    featured = models.BooleanField(default=False)
    template = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='default')
    trailer_url = models.URLField(blank=True, null=True)  # New field for trailer video URL

    github_label = models.CharField(max_length=50, default='GitHub', blank=True)  # Custom label for GitHub button
    live_label = models.CharField(max_length=50, default='Live Demo', blank=True)  # Custom label for live demo button
    download_label = models.CharField(max_length=50, default='Download', blank=True)  # Custom label for download button
    external_label = models.CharField(max_length=50, default='External Page', blank=True)  # Custom label for external link button

    def __str__(self):
        return self.title

class ProjectImage(models.Model):
    image = CloudinaryField('projects/')
    caption = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.caption or "Project Image"

class CV(models.Model):
    resume = CloudinaryField('resume')

    def __str__(self):
        return "CV"

class Profile(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    linkedin = models.URLField()
    github = models.URLField()
    itch_io = models.URLField()
    image = CloudinaryField('profile/', default='profile_default.jpg')
    bio = models.TextField()

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()  # Rich text via Summernote
    image = CloudinaryField('blog/', blank=True, null=True)  # Optional hero image
    video_url = models.URLField(blank=True, null=True)  # Optional YouTube URL
    projects = models.ManyToManyField(
        Project, blank=True, related_name='blog_posts'
    )  # Tag zero or more projects
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    notified = models.BooleanField(default=False)  # True after subscribers are notified
    is_live = models.BooleanField(
        default=False,
        help_text='Only live posts are visible on the site.',
    )
    views = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['-created_on']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class BlogImage(models.Model):
    blog_post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name='images'
    )
    image = CloudinaryField('blog/')
    caption = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.caption or f"Image for {self.blog_post.title}"


class Subscriber(models.Model):
    """Email subscriber for blog post notifications."""
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    subscribe_all = models.BooleanField(
        default=True,
        help_text='Receive notifications for every new blog post.',
    )
    projects = models.ManyToManyField(
        Project, blank=True, related_name='subscribers',
        help_text='If not subscribed to all, only these projects trigger emails.',
    )
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

