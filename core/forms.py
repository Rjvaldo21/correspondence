from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    IncomingLetter, OutgoingLetter,
    Disposition, FollowUp, DispositionAssignment
)

User = get_user_model()


class IncomingLetterForm(forms.ModelForm):
    class Meta:
        model = IncomingLetter
        fields = [
            "received_via", "origin", "origin_number", "origin_date",
            "subject", "priority", "scan_pdf", "classification_tags",
            "attachments",
        ]
        widgets = {
            "origin_date": forms.DateInput(attrs={"type": "date"}),
            "classification_tags": forms.SelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Simpan"))


class DispositionForm(forms.ModelForm):
    """
    Form untuk buat Despacho baru + pilih staf yang akan ditugaskan.
    """
    assignees = forms.ModelMultipleChoiceField(
        label="Hatúr ba staf ne'ebé",
        queryset=User.objects.filter(is_active=True).order_by("username"),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",  # BS4
                "size": 6,
            }
        ),
        help_text="Hili responsavel sira ne'ebé simu tarefa Despacho ne'e.",
    )

    class Meta:
        model = Disposition
        fields = ["note", "due_date", "allow_parallel"]
        labels = {
            "note": "Despacho / Observasaun",
            "due_date": "Data-limite",
            "allow_parallel": "Paralelu?",
        }
        widgets = {
            "note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Hatudu instrusaun/Despacho ba karta ida-ne'e...",
                }
            ),
            "due_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "allow_parallel": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean_due_date(self):
        due = self.cleaned_data.get("due_date")
        if due and due < timezone.now().date():
            raise forms.ValidationError("Data-limite la bele liu ohin/horiseik.")
        return due


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = ["doc_type", "title", "file"]


class OutgoingLetterForm(forms.ModelForm):
    class Meta:
        model = OutgoingLetter
        fields = ["template_type", "subject", "body", "attachments"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 10}),
        }
