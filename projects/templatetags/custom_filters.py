from django import template

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