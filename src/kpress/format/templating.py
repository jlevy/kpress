"""The one Jinja environment for all KPress HTML.

KPress authors HTML in `templates/*.jinja`, never with Python f-strings or string
concatenation (see AGENTS.md → "Rendering"). This module is the single place that
loads and renders those templates, so the rule has exactly one implementation.

Two deliberate properties:

- **Hard failures.** `StrictUndefined` turns a missing or misspelled template
  variable into an immediate `jinja2.UndefinedError` at render time — never a
  silently-empty slot that ships broken HTML.
- **Safe by default.** Autoescape is on, so plain values (text, attribute values)
  are escaped automatically. KPress-generated or host-supplied *markup* is the
  exception and is interpolated through the explicit `| safe` filter in the
  template, which keeps every raw-HTML slot visible and auditable in one place.
"""

from __future__ import annotations

from functools import cache

import jinja2


@cache
def _environment() -> jinja2.Environment:
    """The shared, lazily-built environment (templates are packaged data)."""
    return jinja2.Environment(
        loader=jinja2.PackageLoader("kpress.format", "templates"),
        autoescape=True,
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        auto_reload=False,
        keep_trailing_newline=True,
    )


def render_template(template_name: str, /, **context: object) -> str:
    """Render ``templates/<template_name>`` with ``context``.

    Raises ``jinja2.UndefinedError`` on any undefined/misspelled variable
    (``StrictUndefined``) and ``jinja2.TemplateError`` on any other template
    problem, so rendering failures surface immediately rather than producing
    broken HTML downstream.
    """
    return _environment().get_template(template_name).render(context)
