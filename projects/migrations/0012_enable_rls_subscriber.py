"""
Enable Supabase Row Level Security on the subscriber tables.

Same rationale as 0008 / 0010: lock PostgREST out while Django's
`postgres` role (table owner) bypasses RLS automatically.
"""

from django.db import migrations


TABLES = [
    "projects_subscriber",
    "projects_subscriber_projects",   # M2M through table
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
        ("projects", "0011_blogpost_notified_subscriber"),
    ]

    operations = [
        migrations.RunPython(enable_rls, reverse_code=disable_rls),
    ]

