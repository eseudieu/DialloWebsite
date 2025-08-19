from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from website.models import *


def _phone_number_check(phone_number):
    digits = '1234567890'
    digit_error = "Please enter a valid 10 digit phone number"
    if phone_number == '':
        return ''
    
    if len(phone_number) != 10 and len(phone_number) != 12:
        raise forms.ValidationError(digit_error)
    if len(phone_number) == 10:
        for char in phone_number:
            if char not in digits:
                raise forms.ValidationError(digit_error)
        phone_number = phone_number[:3] + '-' + phone_number[3:6] + '-' + phone_number[6:]
    else:
        for i in range(len(phone_number)):
            if i == 3 or i == 7:
                if phone_number[i] != '-':
                    raise forms.ValidationError(digit_error)
            else:
                if phone_number[i] not in digits:
                    raise forms.ValidationError(digit_error)
    
    return phone_number

class RequestServiceForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ['phone_number', 'service_type', 'description']

        widgets = {
            'phone_number': forms.TextInput(attrs={
                "label": "Cell",
                "class": "form-control",
                "placeholder": "Phone number you want associated with this request",
            }),

            'service_type': forms.Select(attrs={
                "label": "Nature of Service",
                "class": "form-control",
                "placeholder": "Theme of service request",
            }),

            'description': forms.Textarea(attrs={
                "label": "Task Description",
                "class": "form-control",
                "placeholder": "Specific details about the desired task",
            }),
        }

    def clean_phone_number(self):
        return _phone_number_check(self.cleaned_data['phone_number'])
    
class ServiceReviewForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['review_rating', 'review_text']

        widgets = {
            'review_rating': forms.Select(attrs={
                'label': "Satisfaction",
                'class': "form-control",
                'placeholder': 'How was the service?',
            }),
            'review_text': forms.Textarea(attrs={
                'label': "",
                'class': 'form-control',
                'placeholder': 'Describe your thoughts...',
            }),
        }

class AdminTaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['price', 'notes', 'scheduled_date']

        widgets = {
            'price': forms.TextInput(attrs={
                'verbose_name': "Service Cost",
                'class': 'form-control',
                'placeholder': 'Requested cost for service',
                'required': False,
            }),
            'notes': forms.Textarea(attrs={
                'label': "",
                'class': 'form-control',
                'placeholder': 'Leave administrative notes here',
                'required': False,
            }),

            'scheduled_date': forms.SelectDateWidget(empty_label=('YY', 'MONTH', 'DD'), attrs={
                'placeholder': 'Tentative date',
                'required': False,
            }),
        }

class ClientTaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['email', 'phone_number']

        widgets = {
            'email': forms.EmailInput(attrs={
                "label": "Email",
                "class": "form-control",
                "placeholder": "Email you want associated with this request",
            }),

            'phone_number': forms.TextInput(attrs={
                "label": "Cell",
                "class": "form-control",
                "placeholder": "Phone number you want associated with this request",
            }),
        }

    def clean_phone_number(self):
        return _phone_number_check(self.cleaned_data['phone_number'])

class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status', 'paid']

        widgets = {
            'status': forms.Select(attrs={
                'label': "Status",
                'class': "form-control",
                'placeholder': '',
            }),

            'paid': forms.CheckboxInput(attrs={
                "label": "Payment received?",
            }),
        }