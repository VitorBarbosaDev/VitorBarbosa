# AGENTS.md

## Project Overview

Django 4.2 portfolio site for a developer (Vitor Barbosa) showcasing Full Stack and Game projects. Deployed on Heroku with Gunicorn, PostgreSQL (Supabase), and Cloudinary for media. All content is managed via Django Admin—there is no user-facing auth or forms.

## Architecture

- **Single Django app (`projects/`)** — contains all models, views, admin, templates, and custom template tags.
- **`portfolio/`** — Django project config (settings, root URL conf, WSGI).
- **Models**: `Project` (portfolio entries with category/template selectors), `ProjectImage` (M2M gallery images), `Profile` (singleton site owner info), `CV` (singleton resume file), `BlogPost` (blog entries optionally tagged to projects), `BlogImage` (multiple images per blog post).
- **Views are all function-based**, each rendering a specific template. No class-based views, no REST API.
- **Project detail uses dynamic template selection**: `project_detail_{project.template}.html` — templates are `default`, `gallery`, `feature` (see `TEMPLATE_CHOICES` in `projects/models.py` and corresponding files in `projects/templates/projects/`).

## Key Conventions

- **Rich text** via `django-summernote` — `description` (Project) and `bio` (Profile) are HTML fields edited in admin.
- **Images use `CloudinaryField`**, never `ImageField`. Media storage is `cloudinary_storage.storage.MediaCloudinaryStorage`. Static files use WhiteNoise (`whitenoise.storage.CompressedManifestStaticFilesStorage`).
- **Custom template filters** live in `projects/templatetags/custom_filters.py`: `truncate_words`, `youtube_embed` (rewrites YouTube watch URLs to embed), `embed_gifs` (converts Giphy URLs to inline `<img>` tags). Load them with `{% load custom_filters %}`.
- **Bootstrap 5** via CDN (not installed via npm). jQuery 3.5 also loaded from CDN. All custom CSS is in `static/css/style.css`.
- **Dark theme** — background `#121212`, accent `#4caf50`. Follow this color palette when adding UI.
- **All templates extend `projects/templates/projects/base.html`**. Use `{% block content %}` for page body and `{% block extra_scripts %}` for page-specific JS.

## Environment & Configuration

- **`env.py`** sets local dev environment variables (`DATABASE_URL`, `SECRET_KEY`, `CLOUDINARY_URL`, `EMAIL_HOST_*`, `DEVELOPMENT=True`). It is imported only if the file exists. Never commit real secrets — this file is for local dev.
- **`DEBUG`** is `True` only when env var `DEVELOPMENT == "True"`. Production enforces SSL, HSTS, secure cookies.
- **Database**: PostgreSQL via `dj_database_url`. Falls back to SQLite for tests (`if 'test' in sys.argv`).

## Developer Workflow

```bash
# Activate virtualenv (Windows)
.\myenv\Scripts\Activate.ps1

# Run dev server
python manage.py runserver

# Migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Collect static (needed before deploy, not for local dev)
python manage.py collectstatic --noinput

# Run tests (uses SQLite automatically)
python manage.py test
```

- **Heroku deploy**: `Procfile` runs `gunicorn portfolio.wsgi`. Runtime is `python-3.9.18`.
- **Static files after changes**: run `collectstatic` to update `staticfiles/`.

## Adding a New Project Detail Template

1. Add choice to `TEMPLATE_CHOICES` in `projects/models.py`.
2. Create `projects/templates/projects/project_detail_{name}.html` extending `base.html`.
3. The view (`project_detail`) will automatically resolve it — no view changes needed.

## Blog Feature

- **`BlogPost`** can be tagged to zero or more `Project` entries via M2M. Untagged posts represent "side projects."
- Blog list (`/blog/`) supports filtering: `?project=<pk>` for a specific project, `?untagged=1` for side projects only. Paginated (6 per page).
- Blog detail (`/blog/<slug>/`) renders Summernote rich text, embedded YouTube videos (`youtube_embed` filter), Giphy GIFs (`embed_gifs` filter), and a clickable screenshot gallery via `BlogImage`.
- **Project detail pages** automatically show a "Blog Posts About This Project" section when tagged posts exist — no extra config needed.
- Admin uses `SummernoteModelAdmin` for rich text, `filter_horizontal` for project tagging, `prepopulated_fields` for slug, and `BlogImageInline` for screenshots.

## File Reference

| Path | Purpose |
|------|---------|
| `portfolio/settings.py` | All Django config, middleware, installed apps |
| `portfolio/urls.py` | Root URL routing — all routes defined here, not in app |
| `projects/models.py` | All data models |
| `projects/views.py` | All view functions |
| `projects/admin.py` | Admin config with Summernote rich text |
| `projects/templatetags/custom_filters.py` | `embed_gifs`, `youtube_embed`, `truncate_words` |
| `projects/templates/projects/base.html` | Base layout with nav, footer, Bootstrap/jQuery CDN |
| `static/css/style.css` | All custom styles (dark theme) |
| `env.py` | Local-only env vars (not for production) |

