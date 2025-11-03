/**
 * Gestion AJAX du panier pour KefyStore
 */

$(document).ready(function() {
    // Gérer l'ajout au panier en AJAX
    $('form[data-ajax-cart="add-to-cart"]').on('submit', function(e) {
        e.preventDefault();

        const form = $(this);
        const button = form.find('button[type="submit"]');
        const originalText = button.html();

        // Désactiver le bouton pendant la requête
        button.prop('disabled', true);
        button.html('<i class="fas fa-spinner fa-spin me-2"></i>Ajout en cours...');

        // Récupérer l'URL du formulaire
        const actionUrl = form.attr('action');

        // Récupérer les données du formulaire
        const formData = form.serialize() + '&ajax=1';

        $.ajax({
            url: actionUrl,
            type: 'POST',
            data: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                if (response.success) {
                    // Mettre à jour le compteur du panier
                    updateCartBadge(response.cart_count);

                    // Afficher une notification de succès
                    showNotification('success', response.message);

                    // Réinitialiser le bouton
                    button.prop('disabled', false);
                    button.html(originalText);
                }
            },
            error: function(xhr, status, error) {
                console.error('Erreur AJAX:', error);

                // Afficher une notification d'erreur
                showNotification('error', 'Erreur lors de l\'ajout au panier. Veuillez réessayer.');

                // Réinitialiser le bouton
                button.prop('disabled', false);
                button.html(originalText);
            }
        });
    });

    // Gérer la suppression d'un article du panier
    $('.remove-from-cart').on('click', function(e) {
        e.preventDefault();

        const itemId = $(this).data('item-id');
        const button = $(this);

        $.ajax({
            url: `/products/remove-from-cart/${itemId}/`,
            type: 'POST',
            data: {
                'ajax': '1'
            },
            success: function(response) {
                if (response.success) {
                    // Mettre à jour le compteur
                    updateCartBadge(response.cart_count);

                    // Supprimer l'élément de la liste
                    button.closest('.cart-item').fadeOut(300, function() {
                        $(this).remove();
                    });

                    // Afficher une notification
                    showNotification('success', response.message);
                }
            },
            error: function() {
                showNotification('error', 'Erreur lors de la suppression. Veuillez réessayer.');
            }
        });
    });

    // Mettre à jour un article du panier
    $('.update-cart-quantity').on('change', function() {
        const itemId = $(this).data('item-id');
        const quantity = $(this).val();

        $.ajax({
            url: `/products/update-cart-item/${itemId}/`,
            type: 'POST',
            data: {
                'quantity': quantity,
                'ajax': '1'
            },
            success: function(response) {
                if (response.success) {
                    updateCartBadge(response.cart_count);
                    showNotification('success', 'Panier mis à jour.');

                    // Recharger la page du panier pour mettre à jour les totaux
                    if (window.location.pathname.includes('/cart/')) {
                        location.reload();
                    }
                }
            },
            error: function() {
                showNotification('error', 'Erreur lors de la mise à jour. Veuillez réessayer.');
            }
        });
    });

    /**
     * Mettre à jour le badge du panier
     */
    function updateCartBadge(count) {
        // Mettre à jour le badge avec l'ID cart-count
        $('#cart-count').text(count);

        // Mettre à jour aussi les autres badges si présents
        $('.cart-badge, .cart-count-badge').text(count);

        // Afficher ou masquer le badge
        if (count > 0) {
            $('#cart-count, .cart-badge, .cart-count-badge').show();
        } else {
            $('#cart-count, .cart-badge, .cart-count-badge').hide();
        }

        // Mettre à jour le texte du bouton panier
        $('.cart-count-text').text(count + ' articles');
    }

    /**
     * Afficher une notification
     */
    function showNotification(type, message) {
        // Supprimer les notifications existantes
        $('.ajax-notification').remove();

        // Créer la notification
        const notification = $('<div>')
            .addClass('ajax-notification alert alert-' + (type === 'success' ? 'success' : 'danger') + ' alert-dismissible fade show')
            .css({
                'position': 'fixed',
                'top': '20px',
                'right': '20px',
                'z-index': '9999',
                'min-width': '300px',
                'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
            })
            .html(
                '<strong>' + (type === 'success' ? '✅' : '❌') + '</strong> ' + message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
            );

        // Ajouter la notification au body
        $('body').append(notification);

        // Supprimer automatiquement après 3 secondes
        setTimeout(function() {
            notification.fadeOut(300, function() {
                $(this).remove();
            });
        }, 3000);
    }
});
