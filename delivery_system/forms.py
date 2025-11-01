from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DeliveryAddress, DeliveryZone
from .services import DeliveryService


class DeliveryAddressForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une adresse de livraison
    """
    
    class Meta:
        model = DeliveryAddress
        fields = [
            'first_name', 'last_name', 'phone_number',
            'address_line_1', 'address_line_2', 'city',
            'postal_code', 'country', 'is_default'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['country'].initial = 'Côte d\'Ivoire'
    
    def clean_phone_number(self):
        """
        Valide le numéro de téléphone
        """
        phone = self.cleaned_data.get('phone_number')
        if phone:
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 8:
                raise forms.ValidationError(_('Le numéro de téléphone doit contenir au moins 8 chiffres.'))
        return phone
    
    def save(self, commit=True):
        """
        Sauvegarde l'adresse avec la zone de livraison
        """
        address = super().save(commit=False)
        
        if self.user:
            address.user = self.user
            
            # Si c'est l'adresse par défaut, marquer les autres comme non-défaut
            if address.is_default:
                self.user.delivery_addresses.update(is_default=False)
            
            # Déterminer la zone de livraison
            delivery_info = DeliveryService.calculate_delivery_fee(address.city)
            address.zone = delivery_info['zone']
            
            if commit:
                address.save()
        
        return address
