from django.db import models
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