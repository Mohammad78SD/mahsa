from django import template

register = template.Library()

@register.filter(name='persian_numbers')
def persian_numbers(value):
    persian_numbers_map = {
        '0': '۰',
        '1': '۱',
        '2': '۲',
        '3': '۳',
        '4': '۴',
        '5': '۵',
        '6': '۶',
        '7': '۷',
        '8': '۸',
        '9': '۹',
    }
    return ''.join([persian_numbers_map.get(c, c) for c in str(value)])
