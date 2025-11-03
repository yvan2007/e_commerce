from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .models import City, DeliveryAddress, DeliveryZone, Region


class DeliveryService:
    """
    Service pour calculer les frais de livraison selon la zone
    """

    @staticmethod
    def get_delivery_zones():
        """
        Retourne toutes les zones de livraison actives
        """
        return DeliveryZone.objects.filter(is_active=True)

    @staticmethod
    def calculate_delivery_fee(city, country="Côte d'Ivoire"):
        """
        Calcule les frais de livraison selon la ville et le pays
        Support étendu pour toutes les villes de Côte d'Ivoire
        """
        city_lower = city.lower().strip()

        # Mapping des villes vers les types de zones
        cities_to_zones = {
            # Abidjan
            "abidjan": "abidjan",
            "cocody": "abidjan",
            "yopougon": "abidjan",
            "marcory": "abidjan",
            "treichville": "abidjan",
            "adjame": "abidjan",
            "plateau": "abidjan",
            "abobo": "abidjan",
            "anyama": "abidjan",
            "koumassi": "abidjan",
            "port-bouet": "abidjan",
            "bingerville": "abidjan",
            "attécoubé": "abidjan",
            "williamsville": "abidjan",
            "attecoube": "abidjan",
            # Grand-Bassam
            "grand-bassam": "bassam",
            "grand bassam": "bassam",
            "bassam": "bassam",
            "jacqueville": "bassam",
            "bonoua": "bassam",
            # San-Pédro
            "san-pédro": "sanpedro",
            "san pedro": "sanpedro",
            "sanpedro": "sanpedro",
            "sassandra": "sanpedro",
            "tabou": "sanpedro",
            # Yamoussoukro
            "yamoussoukro": "yamoussoukro",
            "yamossoukro": "yamoussoukro",
            "duekoue": "yamoussoukro",
            "duékoué": "yamoussoukro",
            "tabé": "yamoussoukro",
            "bangolo": "yamoussoukro",
            # Bouaké
            "bouaké": "bouake",
            "bouake": "bouake",
            "katiola": "bouake",
            "boundiali": "bouake",
            # Daloa
            "daloa": "daloa",
            "issia": "daloa",
            "oumé": "daloa",
            "oume": "daloa",
            # Korhogo
            "korhogo": "korhogo",
            "tingrela": "korhogo",
            "korogo": "korhogo",
            "ferkessedougou": "korhogo",
            "ferkessédougou": "korhogo",
            "ferkesse": "korhogo",
            # Man
            "man": "man",
            "duékoué": "man",
            "duekoue": "man",
            "guiglo": "man",
            "touba": "man",
            # Gagnoa
            "gagnoa": "gagnoa",
            "ouragahio": "gagnoa",
            # Divo
            "divo": "divo",
            "lakota": "divo",
            # Abengourou
            "abengourou": "abengourou",
            "agboville": "abengourou",
            "agnibilekrou": "abengourou",
            # Odienné
            "odienné": "odienne",
            "odienne": "odienne",
            "seguela": "odienne",
            "séguela": "odienne",
            "madinan": "odienne",
        }

        # Déterminer la zone
        zone_type = cities_to_zones.get(city_lower, "civ_other")

        # Récupérer la zone correspondante
        try:
            zone = DeliveryZone.objects.get(zone_type=zone_type, is_active=True)
        except DeliveryZone.DoesNotExist:
            # Zone par défaut si non trouvée
            zone = DeliveryZone.objects.filter(
                is_active=True, zone_type="civ_other"
            ).first()
            if not zone:
                # Créer une zone par défaut si aucune n'existe
                zone = DeliveryZone.objects.create(
                    name="Zone par défaut",
                    zone_type="civ_other",
                    delivery_fee=4000,
                    estimated_days=5,
                    description="Zone par défaut",
                )

        # Calculer la date de livraison estimée
        estimated_date = timezone.now().date() + timedelta(days=zone.estimated_days)

        return {
            "zone": zone,
            "fee": zone.delivery_fee,
            "estimated_days": zone.estimated_days,
            "estimated_date": estimated_date,
        }

    @staticmethod
    def get_delivery_fee_for_address(address):
        """
        Calcule les frais de livraison pour une adresse donnée

        Args:
            address (DeliveryAddress): Adresse de livraison

        Returns:
            dict: Informations de livraison
        """
        return DeliveryService.calculate_delivery_fee(
            city=address.city, country=address.country
        )

    @staticmethod
    def create_delivery_zones():
        """
        Crée les zones de livraison par défaut si elles n'existent pas
        """
        zones_data = [
            {
                "name": "Abidjan et environs",
                "zone_type": "abidjan",
                "delivery_fee": Decimal("2500.00"),
                "estimated_days": 1,
                "description": "Livraison dans Abidjan et ses communes",
            },
            {
                "name": "Grand-Bassam",
                "zone_type": "bassam",
                "delivery_fee": Decimal("3000.00"),
                "estimated_days": 2,
                "description": "Livraison à Grand-Bassam",
            },
            {
                "name": "Autres villes de Côte d'Ivoire",
                "zone_type": "civ_other",
                "delivery_fee": Decimal("3000.00"),
                "estimated_days": 3,
                "description": "Livraison dans les autres villes de Côte d'Ivoire",
            },
            {
                "name": "International",
                "zone_type": "international",
                "delivery_fee": Decimal("5000.00"),
                "estimated_days": 7,
                "description": "Livraison internationale",
            },
        ]

        for zone_data in zones_data:
            zone, created = DeliveryZone.objects.get_or_create(
                zone_type=zone_data["zone_type"], defaults=zone_data
            )
            if created:
                print(f"Zone créée: {zone.name}")

    @staticmethod
    def get_zone_by_city(city):
        """
        Retourne la zone de livraison correspondant à une ville

        Args:
            city (str): Nom de la ville

        Returns:
            DeliveryZone: Zone de livraison
        """
        city_lower = city.lower().strip()

        # Villes d'Abidjan
        abidjan_cities = [
            "abidjan",
            "cocody",
            "yopougon",
            "marcory",
            "treichville",
            "adjame",
            "plateau",
            "koumassi",
            "attecoube",
            "songon",
            "anyama",
            "bassam",
            "port-bouet",
            "abobo",
            "dabou",
        ]

        if city_lower in abidjan_cities:
            zone_type = "abidjan"
        elif city_lower in ["grand-bassam", "bassam", "grand bassam"]:
            zone_type = "bassam"
        else:
            zone_type = "civ_other"

        try:
            return DeliveryZone.objects.get(zone_type=zone_type, is_active=True)
        except DeliveryZone.DoesNotExist:
            return DeliveryZone.objects.filter(is_active=True).first()

    @staticmethod
    def get_all_regions():
        """
        Retourne toutes les régions actives
        """
        return Region.objects.filter(is_active=True).order_by("name")

    @staticmethod
    def get_cities_by_region(region_id):
        """
        Retourne toutes les villes d'une région
        """
        return City.objects.filter(region_id=region_id, is_active=True).order_by("name")

    @staticmethod
    def get_delivery_fee_for_city(city_name, country="Côte d'Ivoire"):
        """
        Calcule les frais de livraison pour une ville spécifique
        """
        try:
            # Chercher la ville dans la base de données
            city = City.objects.get(name__iexact=city_name, is_active=True)

            # Chercher la zone de livraison associée
            if city.delivery_zones.exists():
                zone = city.delivery_zones.filter(is_active=True).first()
            else:
                # Utiliser la zone par défaut de la région
                zone = DeliveryZone.objects.filter(
                    zone_type="civ_other", is_active=True
                ).first()

            # Calculer la date de livraison
            estimated_date = timezone.now().date() + timedelta(days=zone.estimated_days)

            return {
                "zone": zone,
                "fee": zone.delivery_fee,
                "estimated_days": zone.estimated_days,
                "estimated_date": estimated_date,
                "city": city,
            }
        except City.DoesNotExist:
            # Si la ville n'est pas trouvée, utiliser le calcul par défaut
            return DeliveryService.calculate_delivery_fee(city_name, country)
