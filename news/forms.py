from django import forms
from django.forms import ModelForm
from .models import *


class SavePhrase(forms.ModelForm):
    class Meta:
        model = Phrase
        fields = "__all__"