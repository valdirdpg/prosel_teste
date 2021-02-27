import difflib
import json

from django import template
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import DiffLexer, JsonLexer
from reversion import models

register = template.Library()


@register.simple_tag
def get_old_version(version):
    old = (
        models.Version.objects.get_for_object_reference(
            version.content_type.model_class(), version.object_id
        )
        .filter(id__lt=version.id)
        .first()
    )
    return old


@register.simple_tag
def data_prettified(version):
    """Function to display pretty version of our data"""

    if not version:
        return "[]"

    # Convert the data to sorted, indented JSON
    json_data = json.loads(version.serialized_data)
    response = json.dumps(json_data, sort_keys=True, indent=2)

    # Get the Pygments formatter
    formatter = HtmlFormatter(style="colorful")

    # Highlight the data
    response = highlight(response, JsonLexer(), formatter)

    # Get the stylesheet
    style = "<style>" + formatter.get_style_defs() + "</style><br>"

    # Safe the output
    return mark_safe(style + response)


@register.simple_tag
def diff_data(version, version_old):
    """Function to display pretty version of our data"""

    # Convert the data to sorted, indented JSON
    json_data1 = json.loads(version.serialized_data)
    response1 = json.dumps(json_data1, sort_keys=True, indent=2)

    if version_old:
        json_data2 = json.loads(version_old.serialized_data)
        response2 = json.dumps(json_data2, sort_keys=True, indent=2)
    else:
        response2 = "[]"

    response = difflib.unified_diff(response2.splitlines(), response1.splitlines())
    response = "\n".join(response)
    # Get the Pygments formatter
    formatter = HtmlFormatter(style="colorful")

    # Highlight the data
    response = highlight(response, DiffLexer(), formatter)

    # Get the stylesheet
    style = "<style>" + formatter.get_style_defs() + "</style><br>"

    # Safe the output
    return mark_safe(style + response)
