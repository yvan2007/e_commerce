from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, VendorProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Administration des utilisateurs personnalisée
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_verified', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'email', 'user_type')
        }),
        (_('Contact'), {
            'fields': ('phone_number', 'country_code', 'address', 'city', 'postal_code')
        }),
        (_('Profil'), {
            'fields': ('profile_picture', 'date_of_birth', 'is_verified')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Dates importantes'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile', 'vendor_profile')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Administration des profils utilisateur
    """
    list_display = ('user', 'bio', 'website', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'bio')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('Informations supplémentaires'), {
            'fields': ('bio', 'website', 'social_facebook', 'social_twitter', 'social_instagram')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    """
    Administration des profils vendeurs
    """
    list_display = ('user', 'business_name', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__username', 'user__email', 'business_name', 'business_license')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('Informations de l\'entreprise'), {
            'fields': ('business_name', 'business_description', 'business_license', 'tax_id')
        }),
        (_('Informations financières'), {
            'fields': ('bank_account',)
        }),
        (_('Statut'), {
            'fields': ('is_approved',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_vendors', 'disapprove_vendors']
    
    def approve_vendors(self, request, queryset):
        """Approuver les vendeurs sélectionnés"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} vendeur(s) approuvé(s) avec succès.')
    approve_vendors.short_description = "Approuver les vendeurs sélectionnés"
    
    def disapprove_vendors(self, request, queryset):
        """Désapprouver les vendeurs sélectionnés"""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} vendeur(s) désapprouvé(s) avec succès.')
    disapprove_vendors.short_description = "Désapprouver les vendeurs sélectionnés"