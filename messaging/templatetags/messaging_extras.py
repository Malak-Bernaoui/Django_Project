from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def conversation_other(context, conversation):
    """Return the other participant for the logged-in user."""
    user = context.get('user')
    if not user or not user.is_authenticated:
        return None
    return conversation.get_other_participant(user)
