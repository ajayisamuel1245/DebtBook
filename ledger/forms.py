from django import forms
from django.contrib.auth.models import User
from .models import TraderProfile
from .models import Customer,LedgerEntry


class SignupForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    business_name = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['full_name'],
        )
        return TraderProfile.objects.create(
            user=user,
            business_name=self.cleaned_data['business_name'],
            phone=self.cleaned_data['phone'],
        )


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'notes']
        

class LedgerEntryForm(forms.ModelForm):
    class Meta:
        model = LedgerEntry
        fields = ['customer', 'amount', 'description', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, trader=None, **kwargs):
        super().__init__(*args, **kwargs)
        if trader:
            self.fields['customer'].queryset = Customer.objects.filter(trader=trader)

