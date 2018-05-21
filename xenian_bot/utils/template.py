import os
import re

from htmlmin import minify
from mako.template import Template

from ..settings import TEMPLATE_DIR

__all__ = ['render_template']


def render_template(template_name: str, **kwargs):
    template = Template(filename=os.path.join(TEMPLATE_DIR, template_name))
    rendered_template = template.render(**kwargs)
    minified = re.sub('(<br\s?/?>|\\\\n)', '\n', minify(rendered_template, remove_empty_space=True))
    cleaned = ''
    for part in minified.split('\n'):
        cleaned += part.strip() + '\n'
    return cleaned.strip()
