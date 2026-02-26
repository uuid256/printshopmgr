from django import forms

from accounts.forms import TailwindFormMixin
from .models import Customer, CustomerType


class CustomerForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "customer_type",
            "name",
            "phone",
            "email",
            "is_corporate",
            "tax_id",
            "billing_address",
            "notes",
        ]
        widgets = {
            "billing_address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
