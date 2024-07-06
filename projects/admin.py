from django.contrib import admin
from .models import Project, CV, Profile, ProjectImage
from django_summernote.admin import SummernoteModelAdmin

class ProjectImageInline(admin.TabularInline):
    model = Project.additional_images.through
    extra = 1

class ProjectAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    list_display = ('title', 'category', 'featured', 'template')
    list_filter = ('category', 'featured', 'template')
    search_fields = ('title', 'description')
    ordering = ('category', 'title')
    inlines = [ProjectImageInline]

class CVAdmin(admin.ModelAdmin):
    list_display = ('resume',)

class ProfileAdmin(SummernoteModelAdmin):
    summernote_fields = ('bio',)
    list_display = ('name', 'title', 'email', 'phone')
    search_fields = ('name', 'email', 'title')

admin.site.register(Project, ProjectAdmin)
admin.site.register(CV, CVAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(ProjectImage)