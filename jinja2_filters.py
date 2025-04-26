from markupsafe import Markup


def nl2br(value):
    """
    Convert newlines to <br> tags in text.

    Args:
        value: The string value to convert

    Returns:
        A Markup string with newlines replaced by <br> tags
    """
    if not value:
        return value

    # Replace newlines with <br> tags and mark as safe HTML
    value = Markup(value).replace('\n', Markup('<br>\n'))

    return value


def register_filters(app):
    """
    Register custom filters with Flask app

    Args:
        app: Flask application instance
    """
    app.jinja_env.filters['nl2br'] = nl2br