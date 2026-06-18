from django import forms
from .models import Tenant, Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['branch', 'category', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Sandbox branch choices based on user role
            if user.role == 'TENANT_ADMIN':
                self.fields['branch'].queryset = user.tenant.branches.all()
            else:
                self.fields['branch'].queryset = user.tenant.branches.filter(id=user.branch_id)

class TenantSignupForm(forms.Form):
    CURRENCY_CHOICES = [
        ('UGX', 'UGX - Ugandan Shilling'),
        ('KES', 'KES - Kenyan Shilling'),
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
    ]

    business_name = forms.CharField(max_length=255, label="Business Name")
    admin_full_name = forms.CharField(max_length=255, label="Admin Full Name")
    email = forms.EmailField(label="Admin Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, initial='USD', label="Base Currency")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
