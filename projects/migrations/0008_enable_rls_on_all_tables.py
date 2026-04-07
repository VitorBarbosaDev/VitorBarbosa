"""
Enable Supabase Row Level Security on every Django table.

Supabase exposes all public-schema tables via PostgREST.  With RLS
disabled, anyone who has the project's anon key can read/write every
table through the REST API.

Enabling RLS (without adding any permissive policies) locks PostgREST
out completely.  Django is unaffected because it connects as the
`postgres` role, which is the table owner and therefore **bypasses RLS
by default** in PostgreSQL.

The migration is wrapped in RunPython so it is silently skipped when
the database engine is SQLite (i.e. during `python manage.py test`).
"""

from django.db import migrations, connection


# Every table Django creates in the public schema.
TABLES = [
    "auth_permission",
    "auth_group_permissions",
    "auth_group",
    "auth_user_groups",
    "auth_user_user_permissions",
    "auth_user",
    "django_content_type",
    "django_admin_log",
    "django_migrations",
    "django_session",
    "django_summernote_attachment",
    "projects_project",
    "projects_project_additional_images",
    "projects_projectimage",
    "projects_profile",
    "projects_cv",
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
        ("projects", "0007_project_download_label_project_download_link_and_more"),
    ]

    operations = [
        migrations.RunPython(enable_rls, reverse_code=disable_rls),
    ]

