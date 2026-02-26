from django import forms

from accounts.forms import TailwindFormMixin
from .models import Job


class JobCreateForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "customer",
            "product_type",
            "title",
            "description",
            "quantity",
            "width_cm",
            "height_cm",
            "quoted_price",
            "deposit_amount",
            "discount_amount",
            "due_date",
            "assigned_designer",
            "internal_notes",
        ]
        widgets = {
            "customer": forms.HiddenInput(),
            "description": forms.Textarea(attrs={"rows": 3}),
            "internal_notes": forms.Textarea(attrs={"rows": 2}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
