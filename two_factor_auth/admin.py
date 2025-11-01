"""
Configuration de l'administration pour l'authentification à deux facteurs
"""
from django.contrib import admin
from .models import (
    TwoFactorAuth, TwoFactorCode, TwoFactorSession, TwoFactorDevice
)


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_enabled', 'primary_method', 'totp_verified', 'sms_verified', 'email_verified']
    list_filter = ['is_enabled', 'primary_method', 'totp_verified', 'sms_verified', 'email_verified']
    search_fields = ['user__username', 'user__email', 'phone_number']


@admin.register(TwoFactorCode)
class TwoFactorCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'code_type', 'code', 'is_used', 'expires_at', 'created_at']
    list_filter = ['code_type', 'is_used', 'created_at']
    search_fields = ['user__username', 'code']


@admin.register(TwoFactorSession)
class TwoFactorSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'is_verified', 'ip_address', 'created_at', 'expires_at']
    list_filter = ['is_verified', 'created_at', 'expires_at']
    search_fields = ['user__username', 'session_key', 'ip_address']


@admin.register(TwoFactorDevice)
class TwoFactorDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_name', 'device_type', 'is_trusted', 'is_active', 'last_used']
    list_filter = ['device_type', 'is_trusted', 'is_active', 'last_used']
    search_fields = ['user__username', 'device_name', 'device_fingerprint']