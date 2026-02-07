from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'doc_type', 'google_drive_link', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }