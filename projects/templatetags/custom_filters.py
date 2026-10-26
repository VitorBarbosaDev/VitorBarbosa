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


GIPHY_MEDIA_OR_PAGE_REGEX = re.compile(
    r'https?://(?:(?:media\d*|i)\.giphy\.com/[^\s"\'<>]+\.gif|'
    r'(?:www\.)?giphy\.com/(?:gifs/(?:[\w-]+-)?|embed/)[\w]+)',
    re.IGNORECASE
)


def _get_giphy_embed_src(url):
    """
    Extract the direct image URL from various Giphy URL formats.
    Returns (img_src, link_url) if url is a valid Giphy link, else (None, None).
    """
    if not url:
        return None, None
    url = url.strip()

    # 1. Direct GIF media URLs: media*.giphy.com/media/... or i.giphy.com/...
    if re.match(r'^https?://(?:media\d*|i)\.giphy\.com/[^\s"\'<>]+\.gif', url, re.I):
        return url, url

    # 2. Giphy page URLs: giphy.com/gifs/<slug-or-id> or giphy.com/gifs/<id>
    m = re.match(r'^https?://(?:www\.)?giphy\.com/gifs/(?:[\w-]+-)?([\w]+)/?', url, re.I)
    if m:
        gif_id = m.group(1)
        return f'https://media.giphy.com/media/{gif_id}/giphy.gif', url

    # 3. Giphy embed URLs: giphy.com/embed/<id>
    m = re.match(r'^https?://(?:www\.)?giphy\.com/embed/([\w]+)/?', url, re.I)
    if m:
        gif_id = m.group(1)
        return f'https://media.giphy.com/media/{gif_id}/giphy.gif', url

    return None, None


@register.filter(name='embed_gifs')
def embed_gifs(value):
    """
    Converts Giphy URLs (in anchor tags or standalone in text) to embedded
    responsive images wrapped in link tags. Preserves existing <img> tags.
    """
    if not value or not isinstance(value, str):
        return value

    def _make_gif_html(link_url, img_src):
        return f'<a href="{link_url}" class="gif-link" target="_blank" rel="noopener noreferrer"><img src="{img_src}" alt="GIF" class="img-fluid mb-3 gifs custom-gif"></a>'

    # Step 1: Replace <a ...>...</a> tags that link to Giphy URLs
    def _replace_anchor(match):
        full_tag = match.group(0)
        # If the anchor already contains an <img> tag, do not modify it
        if '<img' in full_tag.lower():
            return full_tag

        href_match = re.search(r'href=["\']([^"\']+)["\']', full_tag, re.I)
        if not href_match:
            return full_tag

        href = href_match.group(1).strip()
        img_src, link_url = _get_giphy_embed_src(href)
        if not img_src:
            return full_tag

        return _make_gif_html(link_url, img_src)

    value = re.sub(r'<a\s+[^>]*>.*?</a>', _replace_anchor, value, flags=re.IGNORECASE | re.DOTALL)

    # Step 2: Replace standalone Giphy URLs in text outside HTML tags
    tokens = re.split(r'(<!--.*?-->|<[^>]+>)', value, flags=re.DOTALL)
    in_anchor = False
    new_tokens = []

    for token in tokens:
        if token.startswith('<') and token.endswith('>'):
            tag_lower = token.lower()
            if tag_lower.startswith('<a ') or tag_lower == '<a>':
                in_anchor = True
            elif tag_lower == '</a>':
                in_anchor = False
            new_tokens.append(token)
        else:
            if not in_anchor and token:
                def _replace_standalone(m):
                    raw_url = m.group(0)
                    # Strip any trailing punctuation that might have been matched
                    clean_url = raw_url
                    trailing = ''
                    while clean_url and clean_url[-1] in '.,;:!?)>"\'':
                        trailing = clean_url[-1] + trailing
                        clean_url = clean_url[:-1]

                    img_src, link_url = _get_giphy_embed_src(clean_url)
                    if img_src:
                        return _make_gif_html(link_url, img_src) + trailing
                    return raw_url

                new_tokens.append(GIPHY_MEDIA_OR_PAGE_REGEX.sub(_replace_standalone, token))
            else:
                new_tokens.append(token)

    return mark_safe(''.join(new_tokens))