import re
from django import template
from django.utils.safestring import mark_safe
from html import unescape
register = template.Library()

@register.filter(name='truncate_words')
def truncate_words(value, word_limit):
    words = value.split()
    if len(words) > word_limit:
        return ' '.join(words[:word_limit]) + '...'
    return value

@register.filter
def youtube_embed(url):
    """
    Extract the YouTube video ID from any common URL format and return
    a clean embed URL.  Handles:
      - https://www.youtube.com/watch?v=VIDEO_ID&si=...
      - https://youtu.be/VIDEO_ID?si=...
      - https://www.youtube.com/embed/VIDEO_ID
      - https://youtube.com/shorts/VIDEO_ID
    """
    if not url:
        return url

    video_id = None

    # youtube.com/watch?v=VIDEO_ID
    match = re.search(r'(?:youtube\.com/watch\?.*v=)([\w-]+)', url)
    if match:
        video_id = match.group(1)

    # youtu.be/VIDEO_ID
    if not video_id:
        match = re.search(r'youtu\.be/([\w-]+)', url)
        if match:
            video_id = match.group(1)

    # youtube.com/embed/VIDEO_ID (already an embed link)
    if not video_id:
        match = re.search(r'youtube\.com/embed/([\w-]+)', url)
        if match:
            video_id = match.group(1)

    # youtube.com/shorts/VIDEO_ID
    if not video_id:
        match = re.search(r'youtube\.com/shorts/([\w-]+)', url)
        if match:
            video_id = match.group(1)

    if video_id:
        return f'https://www.youtube.com/embed/{video_id}'

    # Fallback: return original URL unchanged
    return url


@register.filter(name='embed_gifs')
def embed_gifs(value):
    # Find all GIF URLs in the text
    gif_urls = re.findall(r'(https?://media\.giphy\.com/media/\S+\.gif)', value)

    for url in gif_urls:
        img_tag = f'<img src="{url}" alt="GIF" class="img-fluid mb-3 gifs custom-gif">'

        # Replace URLs within <a> tags first
        value = re.sub(
            rf'(<a[^>]*href="{re.escape(url)}"[^>]*>)(.*?)(</a>)',
            rf'\1{img_tag}<span class="hidden-url">\2</span>\3',
            value
        )

        # Then replace standalone URLs
        value = re.sub(
            rf'\b{re.escape(url)}\b',
            f'<a href="{url}" class="gif-link">{img_tag}</a>',
            value
        )

    return mark_safe(value)