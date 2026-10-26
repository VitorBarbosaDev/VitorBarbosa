"""
Enable Supabase Row Level Security on the OTP MFA tables.

Same rationale as 0008 / 0010 / 0012: lock PostgREST out while Django's
`postgres` role (table owner) bypasses RLS automatically.
"""

from django.db import migrations


TABLES = [
    "otp_totp_totpdevice",
    "otp_static_staticdevice",
    "otp_static_statictoken",
]


def enable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for table in TABLES:
            cursor.execute(
                f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY;'
            )


def disable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for table in TABLES:
            cursor.execute(
                f'ALTER TABLE public."{table}" DISABLE ROW LEVEL SECURITY;'
            )


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0016_blogpost_likes"),
        ("otp_totp", "0003_add_timestamps"),
        ("otp_static", "0003_add_timestamps"),
    ]

    operations = [
        migrations.RunPython(enable_rls, reverse_code=disable_rls),
    ]
