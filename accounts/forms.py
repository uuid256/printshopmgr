"""Shared form utilities for the printshopmgr project."""

from django import forms


_INPUT_CLASSES = (
    "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
)
_CHECKBOX_CLASSES = "rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"


class TailwindFormMixin:
    """Automatically injects Tailwind CSS classes into every widget in the form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", _CHECKBOX_CLASSES)
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault(
                    "class",
                    _INPUT_CLASSES + " resize-none",
                )
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault(
                    "class",
                    _INPUT_CLASSES + " bg-white",
                )
            else:
                widget.attrs.setdefault("class", _INPUT_CLASSES)
