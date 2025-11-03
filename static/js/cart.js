// Fonction pour obtenir le token CSRF
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
           document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
}

// Fonction globale pour ajouter au panier via AJAX
window.addToCartAjax = function(productId, quantity = 1, variantId = null) {
    const formData = new FormData();
    formData.append('quantity', quantity);
    formData.append('csrfmiddlewaretoken', getCSRFToken());
    if (variantId) {
        formData.append('variant_id', variantId);
    }

    return fetch(`/products/add-to-cart/${productId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour le compteur du panier partout sur le site
            const cartCountBadges = document.querySelectorAll('.cart-count-badge, #cart-count, .badge');
            cartCountBadges.forEach(badge => {
                if (badge.textContent.match(/\d+/) || badge.classList.contains('cart-count-badge')) {
                    badge.textContent = data.cart_count;
                }
            });

            // Afficher une notification de succès
            showCartNotification('✅ ' + (data.message || 'Produit ajouté au panier'), 'success');

            // Retourner les données pour utilisation éventuelle
            return data;
        } else {
            showCartNotification('❌ ' + (data.error || 'Erreur lors de l\'ajout au panier'), 'danger');
            throw new Error(data.error);
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showCartNotification('❌ Erreur lors de l\'ajout au panier', 'danger');
        throw error;
    });
};

// Fonction pour afficher les notifications de panier
function showCartNotification(message, type = 'success') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; animation: slideInRight 0.3s ease;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Ajouter au DOM
    document.body.appendChild(notification);

    // Supprimer automatiquement après 3 secondes
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Ajouter les animations CSS si elles n'existent pas
if (!document.querySelector('#cart-animations-style')) {
    const style = document.createElement('style');
    style.id = 'cart-animations-style';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }

        @keyframes slideOutLeft {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(-100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}
