from django.contrib import admin
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from .models import (
    Project, CV, Profile, ProjectImage, BlogPost, BlogImage, Subscriber,
)
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

    class Media:
        css = {
            'all': ('projects/css/admin_custom.css',),
        }

class CVAdmin(admin.ModelAdmin):
    list_display = ('resume',)

class ProfileAdmin(SummernoteModelAdmin):
    summernote_fields = ('bio',)
    list_display = ('name', 'title', 'email', 'phone')
    search_fields = ('name', 'email', 'title')

    class Media:
        css = {
            'all': ('projects/css/admin_custom.css',),
        }

admin.site.register(Project, ProjectAdmin)
admin.site.register(CV, CVAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(ProjectImage)


class BlogImageInline(admin.TabularInline):
    model = BlogImage
    extra = 1


class BlogPostAdmin(SummernoteModelAdmin):
    summernote_fields = ('content',)
    list_display = ('title', 'is_live', 'views', 'created_on', 'updated_on', 'notified')
    list_filter = ('is_live', 'created_on', 'projects', 'notified')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('projects',)
    readonly_fields = ('notified', 'views')
    inlines = [BlogImageInline]
    actions = ['go_live', 'take_offline', 'send_notifications']

    class Media:
        css = {
            'all': ('projects/css/admin_custom.css',),
        }

    @admin.action(description='Go live — publish selected posts')
    def go_live(self, request, queryset):
        updated = queryset.filter(is_live=False).update(is_live=True)
        self.message_user(
            request,
            f'{updated} post(s) are now live.',
        )

    @admin.action(description='Take offline — unpublish selected posts')
    def take_offline(self, request, queryset):
        updated = queryset.filter(is_live=True).update(is_live=False)
        self.message_user(
            request,
            f'{updated} post(s) taken offline.',
        )

    @admin.action(description='Send email notifications to subscribers')
    def send_notifications(self, request, queryset):
        total_sent = 0
        for post in queryset:
            if post.notified:
                self.message_user(
                    request,
                    f'"{post.title}" was already notified — skipped.',
                    level='warning',
                )
                continue

            post_projects = post.projects.all()
            if post_projects.exists():
                subscribers = Subscriber.objects.filter(
                    is_active=True,
                ).filter(
                    Q(subscribe_all=True) | Q(projects__in=post_projects),
                ).distinct()
            else:
                # Untagged post → only "subscribe to all" subscribers
                subscribers = Subscriber.objects.filter(
                    is_active=True, subscribe_all=True,
                )

            for subscriber in subscribers:
                unsub_path = reverse(
                    'unsubscribe', args=[subscriber.token],
                )
                manage_path = reverse(
                    'manage_subscription', args=[subscriber.token],
                )
                unsubscribe_url = request.build_absolute_uri(unsub_path)
                manage_url = request.build_absolute_uri(manage_path)
                post_url = request.build_absolute_uri(
                    reverse('blog_detail', args=[post.slug]),
                )

                context = {
                    'post': post,
                    'post_url': post_url,
                    'unsubscribe_url': unsubscribe_url,
                    'manage_url': manage_url,
                }
                html_body = render_to_string(
                    'projects/emails/new_blogpost.html', context,
                )
                text_body = render_to_string(
                    'projects/emails/new_blogpost.txt', context,
                )

                email = EmailMultiAlternatives(
                    subject=f'New Blog Post: {post.title}',
                    body=text_body,
                    to=[subscriber.email],
                )
                email.attach_alternative(html_body, 'text/html')
                try:
                    email.send(fail_silently=False)
                    total_sent += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f'Failed to email {subscriber.email}: {e}',
                        level='error',
                    )

            post.notified = True
            post.save()

        self.message_user(
            request,
            f'Notifications sent — {total_sent} email(s) delivered.',
        )


admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(BlogImage)


class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribe_all', 'is_active', 'created_on')
    list_filter = ('is_active', 'subscribe_all')
    search_fields = ('email',)
    filter_horizontal = ('projects',)
    readonly_fields = ('token', 'created_on')


admin.site.register(Subscriber, SubscriberAdmin)

