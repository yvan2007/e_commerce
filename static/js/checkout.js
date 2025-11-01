// Fonction pour obtenir le token CSRF
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
}

// Fonction pour charger les régions
async function loadRegions() {
    try {
        const response = await fetch('/orders/api/regions/');
        const data = await response.json();
        
        const regionSelect = document.getElementById('shipping_region');
        regionSelect.innerHTML = '<option value="">Sélectionnez une région</option>';
        
        data.regions.forEach(region => {
            const option = document.createElement('option');
            option.value = region.id;
            option.textContent = region.name;
            regionSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Erreur lors du chargement des régions:', error);
    }
}

// Fonction pour charger les villes d'une région
async function loadCities(regionId) {
    try {
        const response = await fetch(`/orders/api/regions/${regionId}/cities/`);
        const data = await response.json();
        
        const citySelect = document.getElementById('shipping_city');
        citySelect.innerHTML = '<option value="">Sélectionnez une ville</option>';
        
        data.cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city.id;
            option.textContent = city.name;
            citySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Erreur lors du chargement des villes:', error);
    }
}

// Fonction pour calculer les frais de livraison automatiquement pour un pays
async function calculateDeliveryFeeForCountry(country) {
    if (!country) return;
    
    try {
        const response = await fetch('/orders/api/calculate-delivery-fee/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                city: '', // Pas besoin de ville pour les pays hors CIV
                country: country
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('delivery-fee-amount').textContent = data.fee + ' FCFA';
            document.getElementById('delivery-city-name').textContent = country;
            document.getElementById('delivery-fee-display').style.display = 'flex';
            
            // Fonction pour parser les montants correctement
            function parseCurrencyValue(str) {
                let cleaned = str.replace(/[^\d,.\s]/g, '');
                cleaned = cleaned.replace(/\s/g, '');
                cleaned = cleaned.replace(/,/g, '.');
                const digits = cleaned.replace(/[^\d.]/g, '');
                const parts = digits.split('.');
                if (parts.length > 1) {
                    return parseFloat(parts[0] + '.' + parts[1].substring(0, 2));
                }
                return parseFloat(parts[0]);
            }
            
            // Extraire correctement le sous-total
            const subtotalText = document.getElementById('summary-subtotal').textContent;
            const subtotal = parseCurrencyValue(subtotalText);
            
            // Extraire les frais de livraison
            const deliveryFee = parseCurrencyValue(data.fee);
            
            // Calculer le total
            const total = subtotal + deliveryFee;
            
            // Mettre à jour les frais de livraison dans le récapitulatif
            document.getElementById('summary-delivery-fee').textContent = data.fee + ' FCFA';
            document.getElementById('delivery-fee-summary').style.display = 'flex';
            
            // Mettre à jour le champ caché avec les frais de livraison
            document.getElementById('calculated_delivery_fee').value = data.fee;
            
            // Mettre à jour le total avec formatage français
            document.getElementById('summary-total').textContent = total.toLocaleString('fr-FR', {minimumFractionDigits: 0, maximumFractionDigits: 0}) + ' FCFA';
        }
    } catch (error) {
        console.error('Erreur lors du calcul des frais de livraison:', error);
    }
}

// Fonction pour calculer les frais de livraison
async function calculateDeliveryFee() {
    const country = document.getElementById('shipping_country').value;
    const citySelect = document.getElementById('shipping_city');
    const cityIntInput = document.getElementById('shipping_city_int');
    
    let city = '';
    
    if (country === 'Côte d\'Ivoire') {
        const selectedCity = citySelect.options[citySelect.selectedIndex];
        city = selectedCity ? selectedCity.textContent : '';
    } else {
        city = cityIntInput.value;
    }
    
    if (!city) return;
    
    try {
        const response = await fetch('/orders/api/calculate-delivery-fee/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                city: city,
                country: country
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('delivery-fee-amount').textContent = data.fee + ' FCFA';
            document.getElementById('delivery-city-name').textContent = city;
            document.getElementById('delivery-fee-display').style.display = 'flex';
            
            // Fonction pour parser les montants correctement
            function parseCurrencyValue(str) {
                // Supprimer tout sauf chiffres, virgules, points et espaces
                let cleaned = str.replace(/[^\d,.\s]/g, '');
                // Remplacer les espaces (séparateurs de milliers) et les virgules (décimales) par rien
                // On cherche les chiffres uniquement
                cleaned = cleaned.replace(/\s/g, ''); // Enlever les espaces
                cleaned = cleaned.replace(/,/g, '.'); // Remplacer les virgules par des points
                // Extraire uniquement les chiffres et un seul point décimal
                const digits = cleaned.replace(/[^\d.]/g, '');
                // S'il y a un point, garder seulement le premier
                const parts = digits.split('.');
                if (parts.length > 1) {
                    // Il y a des décimales, garder la partie entière
                    return parseFloat(parts[0] + '.' + parts[1].substring(0, 2));
                }
                return parseFloat(parts[0]);
            }
            
            // Extraire correctement le sous-total
            const subtotalText = document.getElementById('summary-subtotal').textContent;
            const subtotal = parseCurrencyValue(subtotalText);
            
            // Extraire les frais de livraison
            const deliveryFee = parseCurrencyValue(data.fee);
            
            // Calculer le total
            const total = subtotal + deliveryFee;
            
            // Mettre à jour les frais de livraison dans le récapitulatif
            document.getElementById('summary-delivery-fee').textContent = data.fee + ' FCFA';
            document.getElementById('delivery-fee-summary').style.display = 'flex';
            
            // Mettre à jour le champ caché avec les frais de livraison
            document.getElementById('calculated_delivery_fee').value = data.fee;
            
            // Mettre à jour le total avec formatage français
            document.getElementById('summary-total').textContent = total.toLocaleString('fr-FR', {minimumFractionDigits: 0, maximumFractionDigits: 0}) + ' FCFA';
        }
    } catch (error) {
        console.error('Erreur lors du calcul des frais de livraison:', error);
    }
}

// Fonction pour charger les méthodes de paiement selon le pays
async function loadPaymentMethods() {
    const country = document.getElementById('shipping_country').value;
    
    try {
        const response = await fetch(`/orders/api/delivery-methods/?country=${country}`);
        const data = await response.json();
        
        const paymentGrid = document.getElementById('payment-methods-grid');
        paymentGrid.innerHTML = '';
        
        const logos = {
            'cash': '/static/images/payment/livraison.png',
            'moovmoney': '/static/images/payment/moov-money.png',
            'orangemoney': '/static/images/payment/orange-money.png',
            'mtnmoney': '/static/images/payment/mtn-money.png',
             'wave': '/static/images/payment/wave.png',
            'carte': '/static/images/payment/carte-bancaire.png',
            'paypal': '/static/images/payment/paypal.png',
            'bank_transfer': '/static/images/payment/bank.png',
        };
        
        data.methods.forEach(method => {
            const div = document.createElement('div');
            div.className = 'payment-option';
            const minHeight = method.value === 'wave' ? '60px' : '55px';
            const specialMinHeight = method.value === 'cash' ? '55px' : minHeight;
            div.innerHTML = `
                <input type="radio" name="payment_method" value="${method.value}" id="payment-${method.value}">
                <label for="payment-${method.value}">
                    <img src="${logos[method.value] || '/static/images/payment/default.png'}" alt="${method.label}" style="min-width: 80px; min-height: ${minHeight}; max-width: 120px; max-height: 80px; object-fit: contain; margin-bottom: 10px; display: block; margin-left: auto; margin-right: auto;">
                    <div>${method.label}</div>
                </label>
            `;
            
            div.addEventListener('click', () => {
                document.querySelectorAll('.payment-option').forEach(opt => opt.classList.remove('active'));
                div.classList.add('active');
                
                // Afficher le formulaire de paiement correspondant
                showPaymentForm(method.value);
            });
            
            paymentGrid.appendChild(div);
        });
    } catch (error) {
        console.error('Erreur lors du chargement des méthodes de paiement:', error);
    }
}

// Fonction pour afficher le formulaire de paiement
function showPaymentForm(method) {
    const container = document.getElementById('payment-forms-container');
    container.innerHTML = '';
    
    let formHTML = '';
    
    switch(method) {
        case 'carte':
            formHTML = `
                <div class="payment-form-details active">
                    <h6 class="mb-3">Informations de la carte</h6>
                    <div class="row">
                        <div class="col-12 mb-3">
                            <label class="form-label">Numéro de carte</label>
                            <input type="text" class="form-control" placeholder="1234 5678 9012 3456">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Date d'expiration</label>
                            <input type="text" class="form-control" placeholder="MM/AA">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">CVV</label>
                            <input type="text" class="form-control" placeholder="123">
                        </div>
                        <div class="col-12 mb-3">
                            <label class="form-label">Titulaire de la carte</label>
                            <input type="text" class="form-control" placeholder="Nom sur la carte">
                        </div>
                    </div>
                </div>
            `;
            break;
        case 'moovmoney':
        case 'orangemoney':
        case 'mtnmoney':
        case 'wave':
            formHTML = `
                <div class="payment-form-details active">
                    <h6 class="mb-3">Informations ${method}</h6>
                    <div class="mb-3">
                        <label class="form-label">Numéro de téléphone</label>
                        <input type="tel" class="form-control" placeholder="+225 XX XX XX XX XX">
                    </div>
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        Vous serez redirigé vers la page de paiement sécurisé de ${method}
                    </div>
                </div>
            `;
            break;
        case 'paypal':
            formHTML = `
                <div class="payment-form-details active">
                    <h6 class="mb-3">Paiement via PayPal</h6>
                    <div class="alert alert-info">
                        <i class="fab fa-paypal me-2"></i>
                        Vous serez redirigé vers PayPal pour finaliser votre paiement
                    </div>
                </div>
            `;
            break;
        case 'bank_transfer':
            formHTML = `
                <div class="payment-form-details active">
                    <h6 class="mb-3">Virement bancaire</h6>
                    <div class="alert alert-warning">
                        <i class="fas fa-info-circle me-2"></i>
                        Vous recevrez les coordonnées bancaires après confirmation de commande
                    </div>
                </div>
            `;
            break;
        default:
            formHTML = '';
    }
    
    container.innerHTML = formHTML;
}

// Gestion du changement de pays
document.getElementById('shipping_country').addEventListener('change', function() {
    const selectedCountry = this.value;
    
    // Afficher/masquer les champs selon le pays
    if (selectedCountry === 'Côte d\'Ivoire') {
        // Champs spécifiques pour la Côte d'Ivoire
        document.getElementById('civ-address-fields').style.display = 'flex';
        document.getElementById('international-address-fields').style.display = 'none';
        
        // Activer les champs région/ville
        const regionField = document.getElementById('shipping_region');
        const cityField = document.getElementById('shipping_city');
        if (regionField) regionField.required = true;
        if (cityField) cityField.required = true;
    } else {
        // Champs pour les autres pays
        document.getElementById('civ-address-fields').style.display = 'none';
        document.getElementById('international-address-fields').style.display = 'flex';
        
        // Désactiver les champs région/ville
        const regionField = document.getElementById('shipping_region');
        const cityField = document.getElementById('shipping_city');
        if (regionField) regionField.required = false;
        if (cityField) cityField.required = false;
    }
    
    // Mettre à jour l'indicatif téléphonique
    updatePhonePrefix(selectedCountry);
    
    loadPaymentMethods();
    
    // Calculer automatiquement les frais de livraison pour les pays hors CIV
    if (selectedCountry !== 'Côte d\'Ivoire') {
        setTimeout(() => calculateDeliveryFeeForCountry(selectedCountry), 500); // Attendre que la ville soit mise à jour
    }
});

// Fonction pour mettre à jour l'indicatif téléphonique et la ville
function updatePhonePrefix(country) {
    const countryCodes = {
        'Côte d\'Ivoire': '+225',
        'Mali': '+223',
        'Burkina Faso': '+226',
        'Sénégal': '+221',
        'Ghana': '+233',
        'Togo': '+228',
        'Bénin': '+229',
        'Guinée': '+224',
        'Niger': '+227',
        'Nigeria': '+234',
        'Cameroun': '+237',
        'Congo': '+242',
        'Gabon': '+241',
        'Tchad': '+235',
        'RCA': '+236',
        'Tunisie': '+216',
        'Maroc': '+212',
        'Algérie': '+213',
        'France': '+33',
        'Belgique': '+32',
    };
    
    const countryCities = {
        'Côte d\'Ivoire': ['Abidjan', 'Yamoussoukro', 'Bouaké', 'Korhogo', 'San-Pédro', 'Daloa', 'Man', 'Gagnoa'],
        'Mali': ['Bamako', 'Sikasso', 'Kayes', 'Ségou', 'Mopti', 'Koulikoro', 'Gao', 'Tombouctou'],
        'Burkina Faso': ['Ouagadougou', 'Bobo-Dioulasso', 'Koudougou', 'Banjforo', 'Dédougou', 'Dori', 'Fada N\'gourma', 'Tenkodogo'],
        'Sénégal': ['Dakar', 'Thiès', 'Saint-Louis', 'Ziguinchor', 'Kaolack', 'Touba', 'Mbour', 'Kédougou'],
        'Ghana': ['Accra', 'Kumasi', 'Tamale', 'Takoradi', 'Ashaiman', 'Sunyani', 'Cape Coast', 'Obuasi'],
        'Togo': ['Lomé', 'Sokodé', 'Kara', 'Atakpamé', 'Dapaong', 'Tsévié', 'Bassar', 'Vogan'],
        'Bénin': ['Cotonou', 'Porto-Novo', 'Parakou', 'Abomey', 'Bohicon', 'Kandi', 'Natitingou', 'Djougou'],
        'Guinée': ['Conakry', 'Nzérékoré', 'Kindia', 'Kankan', 'Guéckédou', 'Mamou', 'Faranah', 'Boké'],
        'Niger': ['Niamey', 'Maradi', 'Zinder', 'Tahoua', 'Dosso', 'Agadez', 'Diffa', 'Tillabéri'],
        'Nigeria': ['Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt', 'Benin City', 'Kaduna', 'Jos'],
        'Cameroun': ['Douala', 'Yaoundé', 'Garoua', 'Bafoussam', 'Bamenda', 'Maroua', 'Buea', 'Kribi'],
        'Congo': ['Brazzaville', 'Pointe-Noire', 'Dolisie', 'Nkayi', 'Ouesso', 'Loandjili', 'Imp fondi', 'Makoua'],
        'Gabon': ['Libreville', 'Port-Gentil', 'Franceville', 'Oyem', 'Moanda', 'Mouila', 'Tchibanga', 'Koulamoutou'],
        'Tchad': ["N'Djamena", 'Moundou', 'Sarh', 'Abéché', 'Doba', 'Ati', 'Lai', 'Kelo'],
        'RCA': ['Bangui', 'Bimbo', 'Berbérati', 'Bossangoa', 'Bambari', 'Kaga-Bandoro', 'Carnot', 'Sibut'],
        'Tunisie': ['Tunis', 'Sfax', 'Sousse', 'Kairouan', 'Gabès', 'Bizerte', 'Ariana', 'Gafsa'],
        'Maroc': ['Casablanca', 'Rabat', 'Marrakech', 'Fès', 'Tanger', 'Meknès', 'Agadir', 'Oujda'],
        'Algérie': ['Alger', 'Oran', 'Constantine', 'Annaba', 'Batna', 'Blida', 'Sétif', 'Djelfa'],
        'France': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 'Montpellier'],
        'Belgique': ['Bruxelles', 'Anvers', 'Gand', 'Charleroi', 'Liège', 'Bruges', 'Namur', 'Louvain'],
    };
    
    const prefixElement = document.getElementById('phone-prefix');
    const code = countryCodes[country] || '+XXX';
    if (prefixElement) {
        prefixElement.textContent = code;
        
        // Mettre à jour le placeholder et rendre l'input éditable pour "Autre"
        const phoneInput = document.getElementById('shipping_phone');
        if (phoneInput) {
            if (country === 'Côte d\'Ivoire') {
                phoneInput.placeholder = '0XXXXXXXXX';
            } else if (country === 'Autre') {
                phoneInput.placeholder = '+XXXXXXXXXX';
            } else {
                phoneInput.placeholder = 'XXXXXXXXXX';
            }
        }
    }
    
    // Mettre à jour la ville pour les pays internationaux
    if (country !== 'Côte d\'Ivoire' && country !== 'Autre') {
        const cityInput = document.getElementById('shipping_city_int');
        if (cityInput) {
            const cities = countryCities[country];
            if (cities && cities.length > 0) {
                // Transformer l'input en select
                const citySelect = document.createElement('select');
                citySelect.id = 'shipping_city_int';
                citySelect.name = 'shipping_city_int';
                citySelect.className = 'form-control';
                citySelect.innerHTML = '<option value="">Sélectionnez une ville</option>';
                
                cities.forEach(city => {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    citySelect.appendChild(option);
                });
                
                // Remplacer l'input par le select
                cityInput.replaceWith(citySelect);
                
                // Définir la première ville comme valeur par défaut
                if (cities.length > 0) {
                    citySelect.value = cities[0];
                }
            }
        }
    } else if (country === 'Autre') {
        // Revenir à un input text pour "Autre pays"
        const cityInput = document.getElementById('shipping_city_int');
        if (cityInput && cityInput.tagName === 'SELECT') {
            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'shipping_city_int';
            input.name = 'shipping_city_int';
            input.className = 'form-control';
            input.placeholder = 'Ville';
            cityInput.replaceWith(input);
        }
    }
}

// Initialiser l'indicatif au chargement
document.addEventListener('DOMContentLoaded', function() {
    const countrySelect = document.getElementById('shipping_country');
    if (countrySelect) {
        updatePhonePrefix(countrySelect.value);
    }
});

// Gestion du changement de région
document.getElementById('shipping_region').addEventListener('change', function() {
    if (this.value) {
        loadCities(this.value);
    }
});

// Gestion du changement de ville
document.getElementById('shipping_city').addEventListener('change', function() {
    // Mettre à jour le champ caché avec le nom de la ville
    const selectedOption = this.options[this.selectedIndex];
    const cityName = selectedOption ? selectedOption.text : '';
    document.getElementById('shipping_city_name').value = cityName;
    
    calculateDeliveryFee();
});

document.getElementById('shipping_city_int').addEventListener('input', function() {
    calculateDeliveryFee();
});

// Écouter les changements sur le select de ville internationale (si créé dynamiquement)
document.addEventListener('change', function(e) {
    if (e.target.id === 'shipping_city_int' && e.target.tagName === 'SELECT') {
        calculateDeliveryFee();
    }
});

// Fonction pour soumettre la commande en AJAX
async function submitOrder(event) {
    event.preventDefault();
    
    // Afficher le loading personnalisé
    showOrderLoading();
    
    const form = document.getElementById('checkout-form');
    const formData = new FormData(form);
    
    // Convertir FormData en objet
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    try {
        const response = await fetch('/orders/api/create-order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Afficher un message de succès
            showLoading('Commande créée avec succès!', 'Redirection...');
            
            // Rediriger vers la page de détails de la commande
            setTimeout(() => {
                window.location.href = `/orders/commande/${result.order_number}/`;
            }, 1000);
        } else {
            hideLoading();
            
            // Afficher les erreurs
            if (result.errors) {
                let errorMessage = 'Erreurs:\n';
                for (let field in result.errors) {
                    errorMessage += `${field}: ${result.errors[field].join(', ')}\n`;
                }
                alert(errorMessage);
            } else {
                alert(result.error || 'Une erreur est survenue lors de la création de votre commande.');
            }
        }
    } catch (error) {
        hideLoading();
        console.error('Erreur:', error);
        alert('Une erreur est survenue. Veuillez réessayer.');
    }
}

// Chargement initial
document.addEventListener('DOMContentLoaded', function() {
    loadRegions();
    loadPaymentMethods();
    
    // Soumission du formulaire en AJAX
    const form = document.getElementById('checkout-form');
    if (form) {
        form.addEventListener('submit', submitOrder);
    }
});
