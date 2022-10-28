from django import forms

class SeatingForm(forms.Form):
    file = forms.FileField( widget=forms.FileInput(attrs={'class': "form-control"}) , required = False)