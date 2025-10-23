from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import (
    IncomingLetter, OutgoingLetter,
    Disposition, FollowUp
)

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
    class Meta:
        model = Disposition
        fields = ["note", "due_date", "allow_parallel", "parent"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

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