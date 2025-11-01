from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, VendorProfile


class UserRegistrationForm(UserCreationForm):
    """
    Formulaire d'inscription pour les utilisateurs
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre adresse email'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom'
        })
    )
    
    phone_number = forms.CharField(
        max_length=17,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre numéro de téléphone'
        })
    )
    
    country_code = forms.ChoiceField(
        choices=User.COUNTRY_CHOICES,
        initial='+225',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Champ caché pour forcer le type client
    user_type = forms.CharField(
        initial='client',
        widget=forms.HiddenInput()
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_("J'accepte les conditions d'utilisation")
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'country_code', 'user_type', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Un utilisateur avec cette adresse email existe déjà."))
        return email
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        country_code = self.cleaned_data.get('country_code')
        
        # Validation basique du numéro de téléphone
        if not phone_number.isdigit():
            raise ValidationError(_("Le numéro de téléphone ne doit contenir que des chiffres."))
        
        # Vérifier l'unicité du numéro complet
        full_phone = f"{country_code}{phone_number}"
        if User.objects.filter(phone_number=phone_number, country_code=country_code).exists():
            raise ValidationError(_("Ce numéro de téléphone est déjà utilisé."))
        
        return phone_number
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.country_code = self.cleaned_data['country_code']
        user.user_type = 'client'  # Forcer le type client
        
        if commit:
            user.save()
            # Créer le profil utilisateur seulement s'il n'existe pas (utilise get_or_create)
            UserProfile.objects.get_or_create(user=user)
        
        return user


class VendorRegistrationForm(UserRegistrationForm):
    """
    Formulaire d'inscription spécialisé pour les vendeurs
    """
    business_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de votre entreprise'
        })
    )
    
    business_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Description de votre entreprise'
        })
    )
    
    business_license = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro de licence (optionnel)'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'country_code', 'password1', 'password2',
                 'business_name', 'business_description', 'business_license')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].initial = 'vendeur'
        self.fields['user_type'].widget = forms.HiddenInput()
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'vendeur'
        
        if commit:
            user.save()
            # Créer le profil utilisateur seulement s'il n'existe pas (utilise get_or_create)
            UserProfile.objects.get_or_create(user=user)
            
            # Créer le profil vendeur seulement s'il n'existe pas
            VendorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'business_name': self.cleaned_data['business_name'],
                    'business_description': self.cleaned_data['business_description'],
                    'business_license': self.cleaned_data['business_license']
                }
            )
        
        return user


class UserLoginForm(AuthenticationForm):
    """
    Formulaire de connexion personnalisé avec possibilité de se connecter avec email ou username
    """
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur ou email',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_("Se souvenir de moi")
    )
    
    def clean_username(self):
        """Permet de se connecter avec email ou username"""
        username = self.cleaned_data['username']
        if '@' in username:
            # C'est un email
            users = User.objects.filter(email=username)
            if not users.exists():
                raise forms.ValidationError(_("Aucun compte n'existe avec cet email."))
            elif users.count() > 1:
                # Plusieurs utilisateurs avec le même email - prendre le plus récent actif
                user = users.filter(is_active=True).order_by('-date_joined').first()
                if not user:
                    user = users.order_by('-date_joined').first()
                if user:
                    return user.username
                raise forms.ValidationError(_("Plusieurs comptes existent avec cet email. Contactez le support."))
            else:
                # Un seul utilisateur trouvé
                return users.first().username
        return username


class UserProfileForm(forms.ModelForm):
    """
    Formulaire de mise à jour du profil utilisateur
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 
                 'country_code', 'address', 'city', 'postal_code', 
                 'date_of_birth', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'country_code': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Un utilisateur avec cette adresse email existe déjà."))
        return email


class VendorProfileForm(forms.ModelForm):
    """
    Formulaire de mise à jour du profil vendeur
    """
    class Meta:
        model = VendorProfile
        fields = ('business_name', 'business_description', 'business_license', 
                 'tax_id', 'bank_account')
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'business_license': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PasswordChangeForm(forms.Form):
    """
    Formulaire de changement de mot de passe
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe actuel'
        })
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        })
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le nouveau mot de passe'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError(_("Le mot de passe actuel est incorrect."))
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError(_("Les mots de passe ne correspondent pas."))
        
        return cleaned_data
    
    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user


class PasswordResetForm(forms.Form):
    """
    Formulaire de réinitialisation de mot de passe
    Note: On ne vérifie pas si l'email existe pour des raisons de sécurité
    (pour ne pas révéler quels emails sont dans la base de données)
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre adresse email'
        })
    )
