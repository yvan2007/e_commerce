// Animations pour les interactions AJAX

// Animation de notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 10000; min-width: 300px; animation: slideInRight 0.3s ease;';
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }, 3000);
}

// Animation de succès pour l'ajout au panier
function showCartAnimation() {
    const cartIcon = document.querySelector('.cart-count-badge');
    if (cartIcon) {
        cartIcon.style.animation = 'bounce 0.5s ease';
        setTimeout(() => {
            cartIcon.style.animation = '';
        }, 500);
    }
}

// Animation de suppression d'élément
function animateElementOut(element, callback) {
    element.style.animation = 'slideOutLeft 0.3s ease';
    setTimeout(() => {
        element.style.opacity = '0';
        element.style.transform = 'translateX(-100%)';
        if (callback) callback();
    }, 300);
}

// Animation de mise à jour de quantité
function animateQuantityUpdate(element) {
    element.style.animation = 'pulse 0.3s ease';
    setTimeout(() => {
        element.style.animation = '';
    }, 300);
}

// Animation de succès
function showSuccessAnimation(element) {
    if (!element) return;

    const successIcon = document.createElement('i');
    successIcon.className = 'fas fa-check-circle text-success';
    successIcon.style.cssText = 'position: absolute; font-size: 2rem; animation: scaleIn 0.3s ease;';

    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(40, 167, 69, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.3s ease;
    `;
    overlay.appendChild(successIcon);

    element.style.position = 'relative';
    element.appendChild(overlay);

    setTimeout(() => {
        overlay.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            overlay.remove();
        }, 300);
    }, 1000);
}

// Styles CSS pour les animations
const animationStyles = `
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

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }

    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.1);
        }
        100% {
            transform: scale(1);
        }
    }

    @keyframes scaleIn {
        from {
            transform: scale(0);
            opacity: 0;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    @keyframes fadeOut {
        from {
            opacity: 1;
        }
        to {
            opacity: 0;
        }
    }

    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }

    .shimmer {
        background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.3) 50%,
            transparent 100%
        );
        background-size: 1000px 100%;
        animation: shimmer 2s infinite;
    }
`;

// Injecter les styles
const styleSheet = document.createElement('style');
styleSheet.textContent = animationStyles;
document.head.appendChild(styleSheet);

// Exporter les fonctions globalement
window.showNotification = showNotification;
window.showCartAnimation = showCartAnimation;
window.animateElementOut = animateElementOut;
window.animateQuantityUpdate = animateQuantityUpdate;
window.showSuccessAnimation = showSuccessAnimation;
