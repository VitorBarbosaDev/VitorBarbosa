from django.db import models
from cloudinary.models import CloudinaryField

class Project(models.Model):
    CATEGORY_CHOICES = [
        ('Full Stack', 'Full Stack'),
        ('Games', 'Games'),
    ]
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = CloudinaryField('projects/', default='default.jpg')
    github_link = models.URLField()
    live_link = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='Full Stack')
    featured = models.BooleanField(default=False)  # New field

    def __str__(self):
        return self.title

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
