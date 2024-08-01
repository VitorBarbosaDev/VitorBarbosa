import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='truncate_words')
def truncate_words(value, word_limit):
    words = value.split()
    if len(words) > word_limit:
        return ' '.join(words[:word_limit]) + '...'
    return value

@register.filter
def youtube_embed(url):
    return url.replace('watch?v=', 'embed/')


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