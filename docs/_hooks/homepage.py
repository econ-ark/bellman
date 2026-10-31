"""Omit documentation scripts from the static homepage."""

import re

from mkdocs.plugins import event_priority


@event_priority(-100)
def on_post_page(output, *, page, config):
    """Remove scripts after plugins have inserted their documentation controls."""
    if page.meta.get("template") != "home.html":
        return output
    return re.sub(r"<script\b[^>]*>.*?</script\s*>", "", output, flags=re.DOTALL | re.IGNORECASE)
