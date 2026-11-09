"""Keep the homepage's media script and omit documentation scripts."""

import re

from mkdocs.plugins import event_priority


@event_priority(-100)
def on_post_page(output, *, page, config):
    """Remove documentation controls after plugins have inserted them."""
    if page.meta.get("template") != "home.html":
        return output
    scripts = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.DOTALL | re.IGNORECASE)
    home_script = re.compile(
        r'<script defer src="(?:\./)?_javascripts/home-scenes\.js" '
        r'data-bellman-home-script></script>'
    )
    return scripts.sub(lambda script: script[0] if home_script.fullmatch(script[0]) else "", output)
