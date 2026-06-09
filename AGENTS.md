# AGENTS.md

## Project Overview

Django 4.2 portfolio site for a developer (Vitor Barbosa) showcasing Full Stack and Game projects. Deployed on Heroku with Gunicorn, PostgreSQL (Supabase), and Cloudinary for media. All content is managed via Django Admin—there is no user-facing auth or forms.

## Architecture

- **Single Django app (`projects/`)** — contains all models, views, admin, templates, and custom template tags.
- **`portfolio/`** — Django project config (settings, root URL conf, WSGI).
- **Models**: `Project` (portfolio entries with category/template selectors), `ProjectImage` (M2M gallery images), `Profile` (singleton site owner info with `itch_io` URL field), `CV` (singleton resume file), `BlogPost` (blog entries optionally tagged to projects, with draft/live workflow and view tracking), `BlogImage` (multiple images per blog post), `Subscriber` (email subscribers for blog notifications).
- **`Project` link/label fields**: `github_link`, `live_link`, `download_link`, `external_link` (all optional URLFields) plus matching label overrides `github_label`, `live_label`, `download_label`, `external_label` (CharField, max 50, each with a sensible default). Also `trailer_url` (optional YouTube URL for a promo trailer).
- **`BlogPost` extra fields**: `image` (optional `CloudinaryField` hero image), `video_url` (optional YouTube URL, passed through `youtube_embed` filter in the template), `is_live` (boolean, default `False` — only live posts are visible on the site), `views` (auto-incremented page-view counter, non-editable).
- **Views are all function-based**, each rendering a specific template. No class-based views, no REST API.
- **Project detail uses dynamic template selection**: `project_detail_{project.template}.html` — templates are `default`, `gallery`, `feature` (see `TEMPLATE_CHOICES` in `projects/models.py` and corresponding files in `projects/templates/projects/`).

## Key Conventions

- **Rich text** via `django-summernote` — `description` (Project) and `bio` (Profile) are HTML fields edited in admin.
- **Images use `CloudinaryField`**, never `ImageField`. Media storage is `cloudinary_storage.storage.MediaCloudinaryStorage`. Static files use WhiteNoise (`whitenoise.storage.CompressedManifestStaticFilesStorage`).
- **Custom template filters** live in `projects/templatetags/custom_filters.py`: `truncate_words`, `youtube_embed` (converts any YouTube URL — `watch?v=`, `youtu.be/`, `/embed/`, `/shorts/` — to a clean embed URL), `embed_gifs` (converts Giphy media URLs to inline `<img>` tags). Load them with `{% load custom_filters %}`.
- **Bootstrap 5** via CDN (not installed via npm). jQuery 3.5, Font Awesome 5, and Google Fonts (Roboto, Lato) are also loaded from CDN in `base.html`. All custom CSS is in `static/css/style.css`.
- **Custom Admin CSS** in `static/projects/css/admin_custom.css` handles mobile responsiveness for Summernote editors in the Django admin.
- **Summernote Configuration** in `portfolio/settings.py` defines the editor toolbar (including font size, color, history, and advanced formatting) and ensures full-width display via custom CSS.
- **Dark theme** — background `#121212`, accent `#4caf50`. Follow this color palette when adding UI.
- **All templates extend `projects/templates/projects/base.html`**. Use `{% block content %}` for page body and `{% block extra_scripts %}` for page-specific JS.

## Environment & Configuration

- **`env.py`** sets local dev environment variables (`DATABASE_URL`, `SECRET_KEY`, `CLOUDINARY_URL`, `EMAIL_HOST_*`, `DEVELOPMENT=True`). It is imported only if the file exists. Never commit real secrets — this file is for local dev.
- **`DEBUG`** is `True` only when env var `DEVELOPMENT == "True"`. Production enforces SSL, HSTS, secure cookies.
- **Database**: PostgreSQL via `dj_database_url`. Falls back to SQLite for tests (`if 'test' in sys.argv`).
- **Supabase RLS**: Row Level Security is enabled on all app tables via `RunPython` migrations (`0008_enable_rls_on_all_tables`, `0010_enable_rls_blog_tables`). When adding new models, create a similar migration that calls `ALTER TABLE public."<table>" ENABLE ROW LEVEL SECURITY;` for each new table — the helper skips execution automatically on SQLite.

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

- **Heroku deploy**: `Procfile` runs `gunicorn portfolio.wsgi`. Runtime is `python-3.12.9`.
- **Static files after changes**: run `collectstatic` to update `staticfiles/`.

## Adding a New Project Detail Template

1. Add choice to `TEMPLATE_CHOICES` in `projects/models.py`.
2. Create `projects/templates/projects/project_detail_{name}.html` extending `base.html`.
3. The view (`project_detail`) will automatically resolve it — no view changes needed.

## Blog Feature

- **`BlogPost`** can be tagged to zero or more `Project` entries via M2M. Untagged posts represent "side projects."
- **Draft/live workflow**: posts default to `is_live=False` (draft). Use the **"Go live"** admin action to publish, or **"Take offline"** to revert. All public queries (`blog_list`, `blog_detail`, `project_detail`) filter on `is_live=True`.
- **View tracking**: `blog_detail` increments `views` atomically via `F()` expression on each page load. The count is displayed in the detail template and visible as a read-only field in admin.
- Blog list (`/blog/`) supports filtering: `?project=<pk>` for a specific project, `?untagged=1` for side projects only. Paginated (6 per page).
- Blog detail (`/blog/<slug>/`) renders Summernote rich text, embedded YouTube videos (`youtube_embed` filter), Giphy GIFs (`embed_gifs` filter), and a clickable screenshot gallery via `BlogImage`.
- **Project detail pages** automatically show a "Blog Posts About This Project" section when tagged **live** posts exist — no extra config needed.
- Admin uses `SummernoteModelAdmin` for rich text, `filter_horizontal` for project tagging, `prepopulated_fields` for slug, and `BlogImageInline` for screenshots. Admin actions: **Go live**, **Take offline**, **Send email notifications**.

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

