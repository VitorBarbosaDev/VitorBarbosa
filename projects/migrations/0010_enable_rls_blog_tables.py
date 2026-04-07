"""
Enable Supabase Row Level Security on the new blog tables.

Same rationale as 0008: lock PostgREST out while Django's `postgres`
role (table owner) bypasses RLS automatically.
"""

from django.db import migrations


TABLES = [
    "projects_blogpost",
    "projects_blogpost_projects",   # M2M through table
    "projects_blogimage",
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
        ("projects", "0009_blogpost_blogimage"),
    ]

    operations = [
        migrations.RunPython(enable_rls, reverse_code=disable_rls),
    ]

