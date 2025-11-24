from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Import your models, including the UserProfile model for reference 
from .models import Product, Order, UserProfile 

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "slug", "image", "description", "price", "stock", "available"]

class OrderCheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email", "address", "postal_code", "city"]

class ShippingProfileForm(forms.ModelForm):
    """Form for users to edit and save their default shipping details."""
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'phone_number',
            'address', 'city', 'postal_code'
        ]        
        labels = {
            'first_name': 'Recipient First Name',
            'last_name': 'Recipient Last Name',
            'phone_number': 'Phone Number',
            'address': 'Street Address',
        }

class SignUpForm(UserCreationForm):
    """Form for standard user (Customer) registration."""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class SellerRegistrationForm(UserCreationForm):
    """Form specifically for Seller registration, used in seller_signup view."""
    email = forms.EmailField(required=True, help_text="Required. Must be a valid email address.")
    
    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        
        # Role assignment (SELLER) and UserProfile creation are handled in the view.
        return user