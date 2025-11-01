from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Pages principales
    path('', views.HomeView.as_view(), name='accounts_home'),
    
    # Authentification
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    
    # Profil utilisateur
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:user_id>/', views.view_user_profile, name='view_user_profile'),
    path('account/', views.account_dashboard, name='account_dashboard'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('delete-account/', views.delete_account_view, name='delete_account'),
    
    # Réinitialisation de mot de passe
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         views.password_reset_confirm_view, 
         name='password_reset_confirm'),
    
    # Confirmation d'email
    path('confirm-email/<uidb64>/<token>/', 
         views.confirm_email_view, 
         name='confirm_email'),
    
    # APIs
    path('api/check-username/', views.check_username_availability, name='check_username'),
    path('api/check-email/', views.check_email_availability, name='check_email'),
    path('api/google-auth/', views.google_auth_view, name='google_auth'),
    
    # URLs pour l'authentification à 2 facteurs
    path('setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('verify-2fa-setup/<str:method>/', views.verify_2fa_setup, name='verify_2fa_setup'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
    path('two-factor-required/', views.two_factor_required, name='two_factor_required'),
    path('send-2fa-code/', views.send_2fa_code, name='send_2fa_code'),
    path('verify-2fa-login/', views.verify_2fa_login, name='verify_2fa_login'),
]
