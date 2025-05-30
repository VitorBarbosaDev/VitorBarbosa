# Generated by Django 4.2.8 on 2024-07-06 14:27

import cloudinary.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0004_alter_profile_image_alter_project_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    cloudinary.models.CloudinaryField(
                        max_length=255, verbose_name="projects/"
                    ),
                ),
                ("caption", models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name="project",
            name="template",
            field=models.CharField(
                choices=[
                    ("default", "Default"),
                    ("gallery", "Gallery"),
                    ("feature", "Feature"),
                ],
                default="default",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="additional_images",
            field=models.ManyToManyField(blank=True, to="projects.projectimage"),
        ),
    ]
