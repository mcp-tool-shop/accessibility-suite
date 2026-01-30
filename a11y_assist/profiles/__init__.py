"""Accessibility profiles for a11y-assist.

Profiles transform AssistResult for different accessibility needs:
- lowvision: Default profile, clear labels and spacing
- cognitive-load: Reduced steps, simplified language, strict limits
- screen-reader: TTS-optimized, expanded abbreviations, no visual references
- dyslexia: Reduced reading friction, explicit labels, no symbolic emphasis
- plain-language: Maximum clarity, one clause per sentence, simple structure
"""

from .cognitive_load import apply_cognitive_load
from .cognitive_load_render import render_cognitive_load
from .dyslexia import apply_dyslexia
from .dyslexia_render import render_dyslexia
from .plain_language import apply_plain_language
from .plain_language_render import render_plain_language
from .screen_reader import apply_screen_reader
from .screen_reader_render import render_screen_reader

__all__ = [
    "apply_cognitive_load",
    "render_cognitive_load",
    "apply_dyslexia",
    "render_dyslexia",
    "apply_plain_language",
    "render_plain_language",
    "apply_screen_reader",
    "render_screen_reader",
]
