from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """{{ my_dict|get_item:key }} — safe dict lookup in templates."""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)
