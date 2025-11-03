// Auth.js - Fonctions d'authentification communes

// Variables globales
let selectedGoogleAccount = null;

// Fonctions Google Sign In
function signInWithGoogle() {
    // Simuler l'ouverture du modal de sélection Google
    const modal = new bootstrap.Modal(document.getElementById('googleAccountModal'));
    modal.show();
}

function selectGoogleAccount(email, name) {
    // Désélectionner tous les comptes
    document.querySelectorAll('.google-account-item').forEach(item => {
        item.classList.remove('selected');
    });

    // Sélectionner le compte cliqué
    event.currentTarget.classList.add('selected');
    selectedGoogleAccount = { email: email, name: name };

    // Mettre à jour le bouton de confirmation
    const confirmBtn = document.querySelector('#googleAccountModal .btn-primary');
    confirmBtn.disabled = false;
    confirmBtn.innerHTML = `<i class="fab fa-google me-2"></i>Se connecter avec ${name}`;
}

function confirmGoogleLogin() {
    if (selectedGoogleAccount) {
        // Envoyer les données à notre API Django
        const formData = new FormData();
        formData.append('email', selectedGoogleAccount.email);
        formData.append('name', selectedGoogleAccount.name);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        fetch('/accounts/api/google-auth/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Afficher le message de succès
                alert(data.message);

                // Fermer le modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('googleAccountModal'));
                modal.hide();

                // Rediriger vers la page d'accueil
                window.location.href = data.redirect_url;
            } else {
                alert('Erreur: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Une erreur est survenue lors de la connexion Google.');
        });
    }
}

// Fonction pour basculer la visibilité du mot de passe
function togglePassword() {
    const passwordInput = document.querySelector('input[name="password"]');
    const toggleIcon = document.getElementById('toggleIcon');

    if (passwordInput && toggleIcon) {
        if (passwordInput.getAttribute('type') === 'password') {
            passwordInput.setAttribute('type', 'text');
            toggleIcon.classList.remove('fa-eye');
            toggleIcon.classList.add('fa-eye-slash');
        } else {
            passwordInput.setAttribute('type', 'password');
            toggleIcon.classList.remove('fa-eye-slash');
            toggleIcon.classList.add('fa-eye');
        }
    }
}

// Fonction pour basculer la visibilité du mot de passe de confirmation
function togglePasswordConfirm() {
    const passwordInput = document.querySelector('input[name="password2"]');
    const toggleIcon = document.getElementById('toggleIconConfirm');

    if (passwordInput && toggleIcon) {
        if (passwordInput.getAttribute('type') === 'password') {
            passwordInput.setAttribute('type', 'text');
            toggleIcon.classList.remove('fa-eye');
            toggleIcon.classList.add('fa-eye-slash');
        } else {
            passwordInput.setAttribute('type', 'password');
            toggleIcon.classList.remove('fa-eye-slash');
            toggleIcon.classList.add('fa-eye');
        }
    }
}

// Validation en temps réel pour l'email
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validation en temps réel pour le nom d'utilisateur
function validateUsername(username) {
    const usernameRegex = /^[a-zA-Z0-9@/./+/-/_]+$/;
    return usernameRegex.test(username) && username.length >= 3;
}

// Fonction pour vérifier la disponibilité de l'email
function checkEmailAvailability(email) {
    if (!email || !validateEmail(email)) return;

    const formData = new FormData();
    formData.append('email', email);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch('/accounts/api/check-email/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const emailInput = document.querySelector('input[name="email"]');
        if (emailInput) {
            if (!data.available) {
                emailInput.classList.add('is-invalid');
                if (!emailInput.nextElementSibling || !emailInput.nextElementSibling.classList.contains('invalid-feedback')) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Cette adresse email est déjà utilisée.';
                    emailInput.parentNode.appendChild(feedback);
                }
            } else {
                emailInput.classList.remove('is-invalid');
                const feedback = emailInput.parentNode.querySelector('.invalid-feedback');
                if (feedback) {
                    feedback.remove();
                }
            }
        }
    })
    .catch(error => {
        console.error('Erreur lors de la vérification de l\'email:', error);
    });
}

// Fonction pour vérifier la disponibilité du nom d'utilisateur
function checkUsernameAvailability(username) {
    if (!username || !validateUsername(username)) return;

    const formData = new FormData();
    formData.append('username', username);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch('/accounts/api/check-username/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const usernameInput = document.querySelector('input[name="username"]');
        if (usernameInput) {
            if (!data.available) {
                usernameInput.classList.add('is-invalid');
                if (!usernameInput.nextElementSibling || !usernameInput.nextElementSibling.classList.contains('invalid-feedback')) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Ce nom d\'utilisateur est déjà pris.';
                    usernameInput.parentNode.appendChild(feedback);
                }
            } else {
                usernameInput.classList.remove('is-invalid');
                const feedback = usernameInput.parentNode.querySelector('.invalid-feedback');
                if (feedback) {
                    feedback.remove();
                }
            }
        }
    })
    .catch(error => {
        console.error('Erreur lors de la vérification du nom d\'utilisateur:', error);
    });
}

// Initialisation des événements
document.addEventListener('DOMContentLoaded', function() {
    // Auto-focus sur le premier champ
    const firstInput = document.querySelector('input[type="text"], input[type="email"]');
    if (firstInput) {
        firstInput.focus();
    }

    // Validation en temps réel pour l'email
    const emailInput = document.querySelector('input[name="email"]');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            checkEmailAvailability(this.value);
        });
    }

    // Validation en temps réel pour le nom d'utilisateur
    const usernameInput = document.querySelector('input[name="username"]');
    if (usernameInput) {
        usernameInput.addEventListener('blur', function() {
            checkUsernameAvailability(this.value);
        });
    }

    // Formatage du numéro de téléphone
    const phoneInput = document.querySelector('input[name="phone_number"]');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            e.target.value = value;
        });
    }
});
