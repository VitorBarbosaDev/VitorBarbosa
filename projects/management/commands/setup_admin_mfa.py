import base64
import io
import qrcode
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken


class Command(BaseCommand):
    help = "Configure MFA (TOTP device and backup recovery tokens) for an admin/staff user."

    def add_arguments(self, parser):
        parser.add_argument(
            "username",
            nargs="?",
            type=str,
            help="Username of the admin/staff user (defaults to sole superuser if only one exists)",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete and recreate TOTP device if one already exists for this user",
        )
        parser.add_argument(
            "--backup-tokens",
            type=int,
            default=5,
            help="Number of emergency static backup tokens to generate (default: 5, 0 to skip)",
        )
        parser.add_argument(
            "--no-qr",
            action="store_true",
            help="Skip ASCII QR code rendering in the terminal output",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = options.get("username")

        if username:
            try:
                user = user_model.objects.get(username=username)
            except user_model.DoesNotExist:
                raise CommandError(f"User '{username}' does not exist.")
        else:
            superusers = list(user_model.objects.filter(is_superuser=True))
            if len(superusers) == 1:
                user = superusers[0]
            elif len(superusers) == 0:
                staff_users = list(user_model.objects.filter(is_staff=True))
                if len(staff_users) == 1:
                    user = staff_users[0]
                elif len(staff_users) == 0:
                    raise CommandError(
                        "No superuser or staff user found. Please create one with 'createsuperuser' first."
                    )
                else:
                    usernames = ", ".join(u.username for u in staff_users)
                    raise CommandError(
                        f"Multiple staff users found ({usernames}). Please specify username: manage.py setup_admin_mfa <username>"
                    )
            else:
                usernames = ", ".join(u.username for u in superusers)
                raise CommandError(
                    f"Multiple superusers found ({usernames}). Please specify username: manage.py setup_admin_mfa <username>"
                )

        if not user.is_staff and not user.is_superuser:
            self.stdout.write(
                self.style.WARNING(
                    f"Warning: User '{user.username}' is not marked as staff or superuser. They will not be able to log in to the admin site until granted staff status."
                )
            )

        # Handle TOTP device
        totp_devices = TOTPDevice.objects.filter(user=user, name="default")
        if options.get("reset") and totp_devices.exists():
            totp_devices.delete()
            self.stdout.write(self.style.NOTICE(f"Existing TOTP device for '{user.username}' reset."))

        totp_device, created = TOTPDevice.objects.get_or_create(
            user=user,
            name="default",
            defaults={"confirmed": True},
        )
        if not created and not totp_device.confirmed:
            totp_device.confirmed = True
            totp_device.save()

        # Secret key (Base32)
        secret_b32 = base64.b32encode(totp_device.bin_key).decode("utf-8")
        config_url = totp_device.config_url

        self.stdout.write(self.style.SUCCESS(f"\n=== MFA Setup for user '{user.username}' ==="))
        self.stdout.write(f"Account:    {user.username}")
        self.stdout.write(f"Secret Key: {secret_b32}")
        self.stdout.write(f"Setup URI:  {config_url}\n")

        # QR Code
        if not options.get("no_qr"):
            self.stdout.write(self.style.HTTP_INFO("Scan this QR code with your Authenticator App (Google Authenticator, Authy, 1Password, etc.):\n"))
            try:
                qr = qrcode.QRCode()
                qr.add_data(config_url)
                qr_io = io.StringIO()
                qr.print_ascii(out=qr_io, invert=True)
                self.stdout.write(qr_io.getvalue())
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not render ASCII QR code: {e}"))

        # Backup static tokens
        num_tokens = options.get("backup_tokens") or 0
        if num_tokens > 0:
            static_device, _ = StaticDevice.objects.get_or_create(
                user=user,
                name="backup",
                defaults={"confirmed": True},
            )
            # Remove existing static tokens and generate fresh ones
            static_device.token_set.all().delete()
            tokens = []
            for _ in range(num_tokens):
                t = static_device.token_set.create(token=StaticToken.random_token())
                tokens.append(t.token)

            self.stdout.write(self.style.SUCCESS(f"\n--- Emergency Backup Recovery Tokens ({num_tokens}) ---"))
            self.stdout.write("Save these single-use recovery codes in a safe place in case you lose access to your authenticator:")
            for idx, token_val in enumerate(tokens, 1):
                self.stdout.write(f"  {idx}. {token_val}")
            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS(f"MFA successfully configured for '{user.username}'!"))
        self.stdout.write("You can now log in at /admin/ using your password + 6-digit TOTP code (or a backup token).\n")
