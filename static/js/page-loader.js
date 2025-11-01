// Gestion du loader de page
(function() {
  'use strict';
  
  let loaderHidden = false;
  let hideTimeout;
  
  // Fonction pour cacher le loader
  function hidePageLoader() {
    if (loaderHidden) return;
    loaderHidden = true;
    
    const pageLoader = document.getElementById('page-loader');
    if (pageLoader) {
      console.log('Hiding page loader');
      // Ajouter la classe hidden qui cache le loader
      pageLoader.classList.add('hidden');
    }
  }
  
  // Fonction pour afficher le loader
  function showPageLoader() {
    const pageLoader = document.getElementById('page-loader');
    if (pageLoader) {
      pageLoader.style.display = 'flex';
      pageLoader.style.opacity = '1';
      pageLoader.style.visibility = 'visible';
      pageLoader.classList.remove('hidden');
    }
  }
  
  // Exposer les fonctions globalement
  window.hidePageLoader = hidePageLoader;
  window.showPageLoader = showPageLoader;
  
  // Afficher le loader immédiatement
  showPageLoader();
  
  // Cacher quand le DOM est prêt avec un délai pour voir l'animation
  document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, hiding loader in 1.5s');
    setTimeout(function() {
      hidePageLoader();
    }, 1500);
  });
  
  // Timeout de sécurité : cache après 4 secondes max (avec animation visible)
  setTimeout(function() {
    console.log('Safety timeout reached, forcing hide');
    hidePageLoader();
  }, 4000);
  
  // Fonctions pour gérer le loading overlay
  window.showLoading = function(title, text) {
    const overlay = document.getElementById('loading-overlay');
    const titleEl = document.getElementById('loading-title');
    const textEl = document.getElementById('loading-text');
    
    if (overlay && titleEl && textEl) {
      if (title) titleEl.textContent = title;
      if (text) textEl.textContent = text;
      overlay.classList.add('active');
    }
  };
  
  window.hideLoading = function() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.classList.remove('active');
    }
  };
  
  // Fonction pour afficher un loading personnalisé
  window.showLoadingMessage = function(message) {
    showLoading('Traitement en cours', message);
  };
  
  // Fonction pour un chargement de paiement
  window.showPaymentLoading = function() {
    showLoading('Traitement du paiement', 'Veuillez patienter, nous traitons votre paiement...');
  };
  
  // Fonction pour un chargement de commande
  window.showOrderLoading = function() {
    showLoading('Création de votre commande', 'Un instant, nous préparons votre commande...');
  };
  
})();

// Intercepter les soumissions de formulaire pour ajouter le loading
document.addEventListener('DOMContentLoaded', function() {
  // Intercepter les liens externes
  document.querySelectorAll('a[href^="http"]').forEach(function(link) {
    link.addEventListener('click', function(e) {
      if (!e.ctrlKey && !e.metaKey) {
        showLoading('Chargement', 'Redirection...');
      }
    });
  });
});

