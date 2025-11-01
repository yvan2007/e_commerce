"""
Formulaires pour le système de popups, captcha et confidentialité
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta

from .models import (
    Popup, CaptchaChallenge, CookieConsent, 
    PrivacyPolicy, TermsOfService, AgeVerification
)


class PopupForm(forms.ModelForm):
    """Formulaire pour créer/modifier les popups"""
    
    class Meta:
        model = Popup
        fields = [
            'name', 'popup_type', 'title', 'content', 'button_text', 'button_url',
            'trigger_type', 'trigger_delay', 'trigger_scroll', 'trigger_time', 'trigger_page_views',
            'show_to_authenticated', 'show_to_anonymous', 'user_types', 'pages',
            'background_color', 'text_color', 'button_color', 'overlay_opacity',
            'is_active', 'start_date', 'end_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'popup_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'button_text': forms.TextInput(attrs={'class': 'form-control'}),
            'button_url': forms.URLInput(attrs={'class': 'form-control'}),
            'trigger_type': forms.Select(attrs={'class': 'form-control'}),
            'trigger_delay': forms.NumberInput(attrs={'class': 'form-control'}),
            'trigger_scroll': forms.NumberInput(attrs={'class': 'form-control'}),
            'trigger_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'trigger_page_views': forms.NumberInput(attrs={'class': 'form-control'}),
            'show_to_authenticated': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_to_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'user_types': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'pages': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Une page par ligne'}),
            'background_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'text_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'button_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'overlay_opacity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")
        
        return cleaned_data


class CaptchaChallengeForm(forms.ModelForm):
    """Formulaire pour créer/modifier les défis captcha"""
    
    class Meta:
        model = CaptchaChallenge
        fields = ['challenge_type', 'question', 'answer', 'options', 'difficulty', 'is_active']
        widgets = {
            'challenge_type': forms.Select(attrs={'class': 'form-control'}),
            'question': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.TextInput(attrs={'class': 'form-control'}),
            'options': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Une option par ligne'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_options(self):
        options = self.cleaned_data.get('options')
        if options:
            # Convertir la liste en JSON si c'est une liste de strings
            if isinstance(options, list):
                return options
            # Sinon, traiter comme du texte séparé par des lignes
            return [option.strip() for option in options.split('\n') if option.strip()]
        return []
    
    def clean(self):
        cleaned_data = super().clean()
        challenge_type = cleaned_data.get('challenge_type')
        options = cleaned_data.get('options')
        
        if challenge_type in ['image', 'checkbox'] and not options:
            raise ValidationError("Les défis de type image et checkbox nécessitent des options.")
        
        return cleaned_data


class CookieConsentForm(forms.ModelForm):
    """Formulaire pour créer/modifier les consentements de cookies"""
    
    class Meta:
        model = CookieConsent
        fields = [
            'name', 'description', 'consent_type', 'is_required', 'is_active',
            'cookie_name', 'cookie_domain', 'cookie_duration'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'consent_type': forms.Select(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cookie_name': forms.TextInput(attrs={'class': 'form-control'}),
            'cookie_domain': forms.TextInput(attrs={'class': 'form-control'}),
            'cookie_duration': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PrivacyPolicyForm(forms.ModelForm):
    """Formulaire pour créer/modifier les politiques de confidentialité"""
    
    class Meta:
        model = PrivacyPolicy
        fields = ['title', 'content', 'version', 'version_type', 'language', 'effective_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 20}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'version_type': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'effective_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class TermsOfServiceForm(forms.ModelForm):
    """Formulaire pour créer/modifier les conditions d'utilisation"""
    
    class Meta:
        model = TermsOfService
        fields = ['title', 'content', 'version', 'version_type', 'language', 'effective_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 20}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'version_type': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'effective_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class AgeVerificationForm(forms.ModelForm):
    """Formulaire pour créer/modifier la vérification d'âge"""
    
    class Meta:
        model = AgeVerification
        fields = [
            'title', 'message', 'min_age', 'is_active', 'show_on_all_pages', 'pages',
            'background_color', 'text_color', 'button_color'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '13', 'max': '25'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_on_all_pages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pages': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Une page par ligne'}),
            'background_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'text_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'button_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class AgeVerificationForm(forms.Form):
    """Formulaire pour la vérification d'âge côté utilisateur"""
    birth_date = forms.DateField(
        label="Date de naissance",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': timezone.now().date().strftime('%Y-%m-%d')
        }),
        help_text="Veuillez entrer votre date de naissance pour vérifier votre âge."
    )
    
    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 13:
                raise ValidationError("Vous devez avoir au moins 13 ans pour utiliser ce site.")
        
        return birth_date


class CaptchaForm(forms.Form):
    """Formulaire pour la résolution du captcha"""
    answer = forms.CharField(
        label="Réponse",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre réponse'
        })
    )
    session_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def clean_answer(self):
        answer = self.cleaned_data.get('answer')
        if not answer or not answer.strip():
            raise ValidationError("Veuillez entrer une réponse.")
        return answer.strip()


class CookieConsentForm(forms.Form):
    """Formulaire pour le consentement aux cookies"""
    necessary = forms.BooleanField(
        label="Cookies nécessaires",
        initial=True,
        disabled=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    analytics = forms.BooleanField(
        label="Cookies analytiques",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    marketing = forms.BooleanField(
        label="Cookies marketing",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    preferences = forms.BooleanField(
        label="Cookies de préférences",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    social = forms.BooleanField(
        label="Cookies réseaux sociaux",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
