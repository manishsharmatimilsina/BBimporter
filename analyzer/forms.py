from django import forms
from .models import AnalysisSession

class AnalysisForm(forms.ModelForm):
    class Meta:
        model = AnalysisSession
        fields = ['session_id']
