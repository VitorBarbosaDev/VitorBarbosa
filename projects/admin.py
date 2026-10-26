import base64
import io
import qrcode
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, strip_tags
from django_otp.admin import OTPAdminSite, OTPAdminAuthenticationForm
from django_otp import devices_for_user, user_has_device
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from .models import (
    Project, CV, Profile, ProjectImage, BlogPost, BlogImage, Subscriber,
)
from django_summernote.admin import SummernoteModelAdmin


class CustomOTPAdminAuthenticationForm(OTPAdminAuthenticationForm):
    """
    Custom OTP Admin authentication form supporting both convenient 1-step login
    (username + password + 6-digit TOTP code) and multi-device selection.
    If the user has not yet configured any OTP devices, allows standard login
    without requiring an OTP token.
    """
    def _chosen_device(self, user):
        device = super()._chosen_device(user)
        if device is None and user is not None:
            devices = list(devices_for_user(user, confirmed=True))
            if len(devices) == 1:
                return devices[0]
            elif len(devices) > 1:
                for d in devices:
                    if 'totp' in d._meta.app_label:
                        return d
                return devices[0]
        return device

    def clean(self):
        self.cleaned_data = super(OTPAdminAuthenticationForm, self).clean()
        user = self.get_user()
        if user is not None and not user_has_device(user, confirmed=True):
            user.otp_device = None
            return self.cleaned_data

        self.clean_otp(user)
        return self.cleaned_data


class CustomOTPAdminSite(OTPAdminSite):
    """
    Custom OTP Admin Site that enforces MFA for users who have configured OTP devices,
    while allowing users who have not yet configured MFA to log in and access the admin
    so they can set up their TOTP devices.
    """
    login_form = CustomOTPAdminAuthenticationForm
    login_template = 'projects/admin_login.html'

    def has_permission(self, request):
        if not super(OTPAdminSite, self).has_permission(request):
            return False
        if not user_has_device(request.user, confirmed=True):
            return True
        return request.user.is_verified()


# Enforce MFA for the Django Admin site
admin.site.__class__ = CustomOTPAdminSite
admin.site.login_form = CustomOTPAdminAuthenticationForm
admin.site.login_template = 'projects/admin_login.html'


class CustomUserAdmin(BaseUserAdmin):
    """
    Custom UserAdmin that integrates Two-Factor Authentication (MFA) setup,
    status badges, scannable QR codes, backup recovery tokens, and 2FA management
    directly into the Django Admin User change view and changelist.
    """
    change_form_template = 'projects/admin_user_change_form.html'

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if 'mfa_security_panel' not in readonly_fields:
            readonly_fields.append('mfa_security_panel')
        return readonly_fields

    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        if 'mfa_status_display' not in list_display:
            list_display.append('mfa_status_display')
        return list_display

    @admin.display(description="2FA / MFA Status")
    def mfa_status_display(self, obj):
        has_mfa = user_has_device(obj, confirmed=True)
        if has_mfa:
            return format_html(
                '<span style="display:inline-block; padding: 2px 8px; border-radius: 12px; background: #2e7d32; color: #ffffff; font-weight: 600; font-size: 11px;">'
                '✓ Active</span>'
            )
        else:
            setup_url = reverse('admin:auth_user_mfa_setup', args=[obj.pk])
            return format_html(
                '<span style="display:inline-block; padding: 2px 8px; border-radius: 12px; background: #616161; color: #ffffff; font-size: 11px;">'
                'Not Set</span> <a href="{}" style="margin-left: 6px; font-size: 11px; font-weight: 600; color: #4caf50;">[+ Add MFA]</a>',
                setup_url
            )

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        if obj:
            fieldsets.append(
                (
                    'Two-Factor Authentication (2FA / MFA)',
                    {
                        'fields': ('mfa_security_panel',),
                        'description': 'Configure Multi-Factor Authentication (authenticator app QR code) to secure this user account.',
                    }
                )
            )
        return fieldsets

    def mfa_security_panel(self, obj):
        if not obj or not obj.pk:
            return "Save user first before configuring 2FA."

        has_mfa = user_has_device(obj, confirmed=True)
        setup_url = reverse('admin:auth_user_mfa_setup', args=[obj.pk])
        backup_url = reverse('admin:auth_user_mfa_backup_tokens', args=[obj.pk])
        disable_url = reverse('admin:auth_user_mfa_disable', args=[obj.pk])

        if has_mfa:
            totp_devices = TOTPDevice.objects.filter(user=obj, confirmed=True)
            device_info = ""
            if totp_devices.exists():
                d = totp_devices.first()
                created = d.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(d, 'created_at') and d.created_at else 'Active'
                device_info = f"Device: <strong>{d.name}</strong> (configured {created})"

            static_tokens_count = 0
            try:
                s_dev = StaticDevice.objects.filter(user=obj, confirmed=True).first()
                if s_dev:
                    static_tokens_count = s_dev.token_set.count()
            except Exception:
                pass

            return format_html(
                '<div style="background: #1b2e1e; border: 1px solid #2e7d32; border-radius: 8px; padding: 16px; margin: 4px 0; color: #e0e0e0;">'
                '  <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">'
                '    <div>'
                '      <span style="display: inline-block; padding: 4px 10px; border-radius: 14px; background: #2e7d32; color: #ffffff; font-weight: bold; font-size: 13px;">'
                '        ✓ Two-Factor Authentication Active'
                '      </span>'
                '      <p style="margin: 8px 0 4px 0; font-size: 13px; color: #b0bec5;">{device_info}</p>'
                '      <p style="margin: 0; font-size: 12px; color: #90a4ae;">Emergency backup recovery tokens remaining: <strong>{static_tokens_count}</strong></p>'
                '    </div>'
                '    <div style="display: flex; gap: 8px; flex-wrap: wrap;">'
                '      <a href="{setup_url}" class="button" style="background: #388e3c; color: white !important; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold;">'
                '        📱 Re-configure / Show QR'
                '      </a>'
                '      <a href="{backup_url}" class="button" style="background: #0288d1; color: white !important; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold;">'
                '        🔑 Backup Recovery Codes'
                '      </a>'
                '      <a href="{disable_url}" class="button" style="background: #d32f2f; color: white !important; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold;">'
                '        ✕ Disable 2FA'
                '      </a>'
                '    </div>'
                '  </div>'
                '</div>',
                device_info=format_html(device_info),
                static_tokens_count=static_tokens_count,
                setup_url=setup_url,
                backup_url=backup_url,
                disable_url=disable_url,
            )
        else:
            return format_html(
                '<div style="background: #2a2415; border: 1px solid #f57c00; border-radius: 8px; padding: 16px; margin: 4px 0; color: #e0e0e0;">'
                '  <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">'
                '    <div style="max-width: 580px;">'
                '      <span style="display: inline-block; padding: 4px 10px; border-radius: 14px; background: #e65100; color: #ffffff; font-weight: bold; font-size: 13px;">'
                '        ⚠ 2FA / MFA Not Configured'
                '      </span>'
                '      <p style="margin: 8px 0 0 0; font-size: 13px; color: #cfd8dc; line-height: 1.4;">'
                '        Add Multi-Factor Authentication (MFA) to this account for extra security. '
                '        You will get an instant <strong>scannable QR code</strong> compatible with Google Authenticator, Authy, Apple Passwords, Microsoft Authenticator, 1Password, and more.'
                '      </p>'
                '    </div>'
                '    <div>'
                '      <a href="{setup_url}" class="button" style="background: #4caf50; color: white !important; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">'
                '        📱 Add MFA to Account (Scan QR Code)'
                '      </a>'
                '    </div>'
                '  </div>'
                '</div>',
                setup_url=setup_url,
            )

    mfa_security_panel.short_description = "Security Status"

    def get_urls(self):
        urls = [
            path(
                '<int:user_id>/mfa/setup/',
                self.admin_site.admin_view(self.mfa_setup_view),
                name='auth_user_mfa_setup',
            ),
            path(
                '<int:user_id>/mfa/backup-tokens/',
                self.admin_site.admin_view(self.mfa_backup_tokens_view),
                name='auth_user_mfa_backup_tokens',
            ),
            path(
                '<int:user_id>/mfa/disable/',
                self.admin_site.admin_view(self.mfa_disable_view),
                name='auth_user_mfa_disable',
            ),
        ] + super().get_urls()
        return urls

    def _check_user_mfa_permission(self, request, user):
        if not (request.user.is_superuser or request.user.has_perm('auth.change_user') or request.user.pk == user.pk):
            raise PermissionDenied("You do not have permission to manage MFA for this user.")

    def mfa_setup_view(self, request, user_id):
        user_obj = get_object_or_404(User, pk=user_id)
        self._check_user_mfa_permission(request, user_obj)

        error = None
        device = None

        if request.method == 'POST':
            device_id = request.POST.get('device_id')
            if device_id:
                device = TOTPDevice.objects.filter(user=user_obj, pk=device_id).first()
            if not device:
                device = TOTPDevice.objects.filter(user=user_obj, confirmed=False).first()
            if not device:
                device = TOTPDevice.objects.filter(user=user_obj, confirmed=True).first()
            if not device:
                device = TOTPDevice.objects.create(
                    user=user_obj,
                    name='default',
                    confirmed=False,
                )

            token = request.POST.get('otp_token', '').strip().replace(' ', '')
            if not token:
                error = "Please enter the 6-digit code from your authenticator app."
            elif device.verify_token(token):
                device.confirmed = True
                device.save()
                # Clean up any other duplicate TOTP devices for this user
                TOTPDevice.objects.filter(user=user_obj).exclude(pk=device.pk).delete()

                # Generate emergency backup recovery tokens
                static_dev, _ = StaticDevice.objects.get_or_create(
                    user=user_obj,
                    name='backup',
                    defaults={'confirmed': True},
                )
                if not static_dev.confirmed:
                    static_dev.confirmed = True
                    static_dev.save()

                static_dev.token_set.all().delete()
                backup_tokens = []
                for _ in range(8):
                    t = static_dev.token_set.create(token=StaticToken.random_token())
                    backup_tokens.append(t.token)

                # If current user is setting up their own MFA, mark current session as OTP verified
                if request.user.pk == user_obj.pk:
                    import django_otp
                    django_otp.login(request, device)

                self.message_user(
                    request,
                    f"Two-Factor Authentication successfully enabled for {user_obj.username}.",
                )
                context = dict(
                    self.admin_site.each_context(request),
                    title=f"2FA Enabled — {user_obj.username}",
                    user_obj=user_obj,
                    backup_tokens=backup_tokens,
                    user_url=reverse('admin:auth_user_change', args=[user_obj.pk]),
                )
                return TemplateResponse(request, 'projects/admin_mfa_success.html', context)
            else:
                error = "Invalid code. Please ensure your device clock is synchronized and enter the current 6-digit code."

        if not device:
            confirmed_device = TOTPDevice.objects.filter(user=user_obj, confirmed=True).first()
            is_reset = request.GET.get('reset') == '1'

            if confirmed_device and not is_reset:
                device = confirmed_device
            else:
                device = TOTPDevice.objects.filter(user=user_obj, confirmed=False).first()
                if not device:
                    device = TOTPDevice.objects.create(
                        user=user_obj,
                        name='default',
                        confirmed=False,
                    )

        # Generate QR code PNG Data URI
        img = qrcode.make(device.config_url)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        qr_code_data_uri = f"data:image/png;base64,{qr_b64}"

        # Base32 Secret Key
        secret_raw = base64.b32encode(device.bin_key).decode('utf-8')
        secret_formatted = ' '.join([secret_raw[i:i+4] for i in range(0, len(secret_raw), 4)])
        issuer = getattr(settings, 'OTP_TOTP_ISSUER', 'Vitor Barbosa Portfolio')

        context = dict(
            self.admin_site.each_context(request),
            title=f"Two-Factor Authentication Setup — {user_obj.username}",
            user_obj=user_obj,
            device=device,
            qr_code_data_uri=qr_code_data_uri,
            secret_key_b32=secret_formatted,
            secret_key_raw=secret_raw,
            issuer=issuer,
            error=error,
            is_already_confirmed=device.confirmed,
            user_url=reverse('admin:auth_user_change', args=[user_obj.pk]),
        )
        return TemplateResponse(request, 'projects/admin_mfa_setup.html', context)

    def mfa_backup_tokens_view(self, request, user_id):
        user_obj = get_object_or_404(User, pk=user_id)
        self._check_user_mfa_permission(request, user_obj)

        static_dev, _ = StaticDevice.objects.get_or_create(
            user=user_obj,
            name='backup',
            defaults={'confirmed': True},
        )
        if not static_dev.confirmed:
            static_dev.confirmed = True
            static_dev.save()

        if request.method == 'POST' and request.POST.get('action') == 'generate':
            static_dev.token_set.all().delete()
            for _ in range(8):
                static_dev.token_set.create(token=StaticToken.random_token())
            self.message_user(
                request,
                f"Generated 8 new backup recovery tokens for {user_obj.username}.",
            )

        tokens = list(static_dev.token_set.values_list('token', flat=True))

        context = dict(
            self.admin_site.each_context(request),
            title=f"Emergency Backup Tokens — {user_obj.username}",
            user_obj=user_obj,
            backup_tokens=tokens,
            user_url=reverse('admin:auth_user_change', args=[user_obj.pk]),
        )
        return TemplateResponse(request, 'projects/admin_mfa_backup_tokens.html', context)

    def mfa_disable_view(self, request, user_id):
        user_obj = get_object_or_404(User, pk=user_id)
        self._check_user_mfa_permission(request, user_obj)

        if request.method == 'POST':
            TOTPDevice.objects.filter(user=user_obj).delete()
            StaticDevice.objects.filter(user=user_obj).delete()
            self.message_user(
                request,
                f"Two-Factor Authentication has been disabled for {user_obj.username}.",
            )
            return redirect(reverse('admin:auth_user_change', args=[user_obj.pk]))

        context = dict(
            self.admin_site.each_context(request),
            title=f"Disable 2FA — {user_obj.username}",
            user_obj=user_obj,
            user_url=reverse('admin:auth_user_change', args=[user_obj.pk]),
        )
        return TemplateResponse(request, 'projects/admin_mfa_disable_confirm.html', context)


if admin.site.is_registered(User):
    admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class ProjectImageInline(admin.TabularInline):
    model = Project.additional_images.through
    extra = 1

class ProjectAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    list_display = ('title', 'slug', 'category', 'featured', 'template')
    list_filter = ('category', 'featured', 'template')
    list_editable = ('featured',)
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('category', 'title')
    inlines = [ProjectImageInline]
    actions = ['make_featured', 'remove_featured']

    @admin.action(description='Mark selected projects as featured')
    def make_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} project(s) marked as featured.')

    @admin.action(description='Unmark selected projects as featured')
    def remove_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} project(s) removed from featured.')

    class Media:
        css = {
            'all': ('projects/css/admin_custom.css',),
        }
        js = ('projects/js/admin_custom.js',)

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
        js = ('projects/js/admin_custom.js',)

admin.site.register(Project, ProjectAdmin)
admin.site.register(CV, CVAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(ProjectImage)


class BlogImageInline(admin.TabularInline):
    model = BlogImage
    extra = 1


class BlogPostAdmin(SummernoteModelAdmin):
    summernote_fields = ('content',)
    list_display = ('title', 'featured', 'is_live', 'views', 'likes', 'created_on', 'updated_on', 'notified')
    list_filter = ('featured', 'is_live', 'created_on', 'projects', 'notified')
    list_editable = ('featured',)
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('projects',)
    readonly_fields = ('notified', 'views', 'likes')
    inlines = [BlogImageInline]
    actions = ['go_live', 'take_offline', 'make_featured', 'remove_featured', 'send_notifications']

    class Media:
        css = {
            'all': ('projects/css/admin_custom.css',),
        }
        js = ('projects/js/admin_custom.js',)

    @admin.action(description='Feature selected posts')
    def make_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} post(s) marked as featured.')

    @admin.action(description='Unfeature selected posts')
    def remove_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} post(s) removed from featured.')

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

