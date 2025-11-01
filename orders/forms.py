from django import forms
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from delivery_system.models import DeliveryAddress, DeliveryZone
from delivery_system.services import DeliveryService
from .models import ShippingAddress, Order


class CheckoutForm(forms.Form):
    """
    Formulaire pour le processus de commande
    """
    
    # Informations de livraison
    shipping_first_name = forms.CharField(
        max_length=50,
        label=_("Prénom"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre prénom')
        })
    )
    
    shipping_last_name = forms.CharField(
        max_length=50,
        label=_("Nom"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre nom')
        })
    )
    
    shipping_phone = forms.CharField(
        max_length=20,
        label=_("Téléphone"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre numéro de téléphone')
        })
    )
    
    shipping_address = forms.CharField(
        max_length=255,
        label=_("Adresse"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre adresse complète')
        })
    )
    
    shipping_city = forms.CharField(
        max_length=100,
        label=_("Ville"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre ville'),
            'id': 'shipping_city'
        })
    )
    
    shipping_postal_code = forms.CharField(
        max_length=20,
        required=False,
        label=_("Code postal"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Code postal (optionnel)')
        })
    )
    
    shipping_country = forms.CharField(
        max_length=100,
        initial='Côte d\'Ivoire',
        label=_("Pays"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True
        })
    )
    
    shipping_city_int = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.HiddenInput()
    )
    
    shipping_city_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.HiddenInput()
    )
    
    shipping_region = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.HiddenInput()
    )
    
    # Champ pour stocker les frais de livraison calculés
    calculated_delivery_fee = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    # Méthode de paiement
    PAYMENT_METHODS = [
        ('cash', _('Cash à la livraison')),
        ('moovmoney', _('Moov Money')),
        ('orangemoney', _('Orange Money')),
        ('mtnmoney', _('MTN Money')),
        ('wave', _('Wave')),
        ('carte', _('Carte bancaire')),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        label=_("Méthode de paiement"),
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    # Options supplémentaires
    save_address = forms.BooleanField(
        required=False,
        label=_("Sauvegarder cette adresse"),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    notes = forms.CharField(
        required=False,
        label=_("Notes de commande"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Instructions spéciales pour la livraison...')
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pré-remplir avec les informations de l'utilisateur si disponible
        if self.user and self.user.is_authenticated:
            # Informations personnelles de base depuis le profil utilisateur
            self.fields['shipping_first_name'].initial = self.user.first_name or ''
            self.fields['shipping_last_name'].initial = self.user.last_name or ''
            
            # Téléphone depuis le profil
            if hasattr(self.user, 'phone_number') and self.user.phone_number:
                self.fields['shipping_phone'].initial = self.user.phone_number
            elif hasattr(self.user, 'get_full_phone_number'):
                self.fields['shipping_phone'].initial = self.user.get_full_phone_number()
            
            # Adresses par défaut
            address_found = False
            
            # 1. Essayer ShippingAddress
            try:
                default_shipping = self.user.shipping_addresses.get(is_default=True)
                self.fields['shipping_address'].initial = default_shipping.address
                self.fields['shipping_city'].initial = default_shipping.city
                if hasattr(self, 'fields') and 'shipping_postal_code' in self.fields:
                    self.fields['shipping_postal_code'].initial = default_shipping.postal_code
                if hasattr(self, 'fields') and 'shipping_country' in self.fields:
                    self.fields['shipping_country'].initial = default_shipping.country or 'Côte d\'Ivoire'
                address_found = True
            except Exception:
                pass
            
            # 2. Sinon essayer DeliveryAddress
            if not address_found:
                try:
                    default_delivery = self.user.delivery_addresses.get(is_default=True)
                    self.fields['shipping_address'].initial = default_delivery.address_line_1
                    self.fields['shipping_city'].initial = default_delivery.city
                    if hasattr(self, 'fields') and 'shipping_postal_code' in self.fields:
                        self.fields['shipping_postal_code'].initial = default_delivery.postal_code or ''
                    if hasattr(self, 'fields') and 'shipping_country' in self.fields:
                        self.fields['shipping_country'].initial = default_delivery.country or 'Côte d\'Ivoire'
                    address_found = True
                except Exception:
                    pass
            
            # 3. Utiliser les champs du UserProfile
            if not address_found:
                if hasattr(self.user, 'profile') and self.user.profile:
                    profile = self.user.profile
                    if hasattr(profile, 'address') and profile.address:
                        self.fields['shipping_address'].initial = profile.address
                    if hasattr(profile, 'city') and profile.city:
                        self.fields['shipping_city'].initial = profile.city
                
                # Champs directs du User
                elif hasattr(self.user, 'city') and self.user.city:
                    self.fields['shipping_city'].initial = self.user.city
                if hasattr(self.user, 'address') and self.user.address:
                    self.fields['shipping_address'].initial = self.user.address
                if hasattr(self.user, 'region') and self.user.region:
                    # Mettre la région comme adresse si pas d'adresse spécifique
                    if 'shipping_address' in self.fields and not self.fields['shipping_address'].initial:
                        self.fields['shipping_address'].initial = self.user.region
    
    def clean_shipping_phone(self):
        """
        Valide le numéro de téléphone et ajoute l'indicatif si nécessaire
        """
        phone = self.cleaned_data.get('shipping_phone')
        country = self.cleaned_data.get('shipping_country', 'Côte d\'Ivoire')
        
        if phone:
            # Extraire uniquement les chiffres
            digits_only = ''.join(filter(str.isdigit, phone))
            
            # Vérifier la longueur minimale
            if len(digits_only) < 8:
                raise forms.ValidationError(_('Le numéro de téléphone doit contenir au moins 8 chiffres.'))
            
            # Ajouter l'indicatif selon le pays
            country_codes = {
                'Côte d\'Ivoire': '+225',
                'Mali': '+223',
                'Burkina Faso': '+226',
                'Sénégal': '+221',
                'Ghana': '+233',
                'Togo': '+228',
                'Bénin': '+229',
                'Guinée': '+224',
                'Niger': '+227',
                'Nigeria': '+234',
                'Cameroun': '+237',
                'Congo': '+242',
                'Gabon': '+241',
                'Tchad': '+235',
                'RCA': '+236',
                'Tunisie': '+216',
                'Maroc': '+212',
                'Algérie': '+213',
                'France': '+33',
                'Belgique': '+32',
            }
            
            code = country_codes.get(country, '')
            if code:
                return f"{code}{digits_only}"
            else:
                # Pour "Autre pays", retourner avec un + par défaut
                return f"+{digits_only}"
        
        return phone
    
    def clean_shipping_city(self):
        """
        Valide la ville et détermine la zone de livraison
        """
        city = self.cleaned_data.get('shipping_city')
        if city:
            # Vérifier que la ville existe dans nos zones
            delivery_info = DeliveryService.calculate_delivery_fee(city)
            if not delivery_info['zone']:
                raise forms.ValidationError(_('Nous ne livrons pas dans cette ville pour le moment.'))
        return city
    
    def save_delivery_address(self):
        """
        Sauvegarde l'adresse de livraison si demandé
        """
        if self.cleaned_data.get('save_address') and self.user:
            # Marquer les autres adresses comme non-défaut
            self.user.delivery_addresses.update(is_default=False)
            
            # Créer la nouvelle adresse
            address = DeliveryAddress.objects.create(
                user=self.user,
                first_name=self.cleaned_data['shipping_first_name'],
                last_name=self.cleaned_data['shipping_last_name'],
                phone_number=self.cleaned_data['shipping_phone'],
                address_line_1=self.cleaned_data['shipping_address'],
                city=self.cleaned_data['shipping_city'],
                postal_code=self.cleaned_data.get('shipping_postal_code'),
                country=self.cleaned_data['shipping_country'],
                is_default=True
            )
            
            # Déterminer la zone de livraison
            delivery_info = DeliveryService.calculate_delivery_fee(address.city)
            address.zone = delivery_info['zone']
            address.save()
            
            return address
        return None


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


class OrderStatusUpdateForm(forms.ModelForm):
    """
    Formulaire pour mettre à jour le statut d'une commande
    """
    
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }
    
    notes = forms.CharField(
        required=False,
        label=_("Notes"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Notes sur le changement de statut...')
        })
    )


class OrderSearchForm(forms.Form):
    """
    Formulaire de recherche pour les commandes
    """
    
    query = forms.CharField(
        required=False,
        label=_("Rechercher"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Numéro de commande, nom, email...')
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        label=_("Statut"),
        choices=[('', _('Tous les statuts'))] + Order.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        label=_("Date de début"),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label=_("Date de fin"),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )