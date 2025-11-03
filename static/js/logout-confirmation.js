/**
 * Script pour demander confirmation avant déconnexion
 * Intercepte TOUS les liens, boutons et actions de déconnexion
 */

(function() {
    'use strict';

    // Fonction pour afficher la confirmation
    function confirmLogout() {
        return confirm('Êtes-vous sûr de vouloir vous déconnecter ?');
    }

    // Intercepter tous les liens de déconnexion au chargement
    document.addEventListener('DOMContentLoaded', function() {
        // Trouver tous les liens qui contiennent "logout" dans l'href
        const allLinks = document.querySelectorAll('a');

        allLinks.forEach(function(link) {
            const href = link.href || link.getAttribute('href') || '';

            if (href.includes('/accounts/logout/') ||
                href.includes('/logout/') ||
                link.classList.contains('logout-btn') ||
                link.classList.contains('logout-link') ||
                link.textContent.toLowerCase().includes('déconnexion') ||
                link.textContent.toLowerCase().includes('logout')) {

                // Ajouter la classe pour identification
                link.classList.add('logout-btn');

                // Intercepter le clic
                link.addEventListener('click', function(event) {
                    if (!confirmLogout()) {
                        event.preventDefault();
                        event.stopPropagation();
                        event.stopImmediatePropagation();
                        return false;
                    }
                });
            }
        });
    });

    // Intercepter les clics sur toute la page (capture)
    document.addEventListener('click', function(event) {
        let target = event.target;
        let link = target;

        // Chercher le lien dans les parents
        while (link && link.tagName !== 'A' && link.tagName !== 'BUTTON' && link !== document.body) {
            link = link.parentElement;
        }

        if (link) {
            const href = link.href || link.getAttribute('href') || '';
            const text = link.textContent || '';

            // Vérifier si c'est un lien de déconnexion
            if ((href && (href.includes('/accounts/logout/') || href.includes('/logout/'))) ||
                link.classList.contains('logout-btn') ||
                link.classList.contains('logout-link') ||
                text.toLowerCase().includes('déconnexion') ||
                text.toLowerCase().includes('se déconnecter') ||
                text.toLowerCase().includes('logout')) {

                if (!confirmLogout()) {
                    event.preventDefault();
                    event.stopPropagation();
                    return false;
                }
            }
        }
    }, true); // Capture phase

    // Fonction globale pour déconnexion programmée
    window.confirmLogout = function(url) {
        if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
            if (url) {
                window.location.href = url;
            } else {
                window.location.href = '/accounts/logout/';
            }
        }
    };

    // Intercepter les formulaires de déconnexion
    document.addEventListener('submit', function(event) {
        const form = event.target;
        const action = form.action || '';

        if (action.includes('logout') || action.includes('/accounts/logout/')) {
            if (!confirmLogout()) {
                event.preventDefault();
                return false;
            }
        }
    }, true);
})();
