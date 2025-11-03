"""
Commande Django pour créer les régions et villes de Côte d'Ivoire pour KefyStore
"""
from django.core.management.base import BaseCommand

from delivery_system.models import City, Region


class Command(BaseCommand):
    help = "Créer les régions et villes de Côte d'Ivoire"

    def handle(self, *args, **options):
        self.stdout.write("Creation des regions et villes de Cote d'Ivoire...")

        # Données des régions et villes de Côte d'Ivoire
        regions_data = [
            {
                "name": "Abidjan",
                "code": "ABI",
                "cities": [
                    "Abidjan",
                    "Cocody",
                    "Marcory",
                    "Treichville",
                    "Adjame",
                    "Plateau",
                    "Koumassi",
                    "Attecoube",
                    "Yopougon",
                    "Abobo",
                    "Anyama",
                    "Songon",
                    "Port-Bouet",
                    "Dabou",
                ],
            },
            {
                "name": "Bafing",
                "code": "BAFIN",
                "cities": [
                    "Touba",
                    "Koro",
                ],
            },
            {
                "name": "Bagoué",
                "code": "BAGOU",
                "cities": [
                    "Boundiali",
                    "Kouto",
                ],
            },
            {
                "name": "Bas-Sassandra",
                "code": "BAS",
                "cities": [
                    "San-Pédro",
                    "Sassandra",
                    "Soubré",
                    "Buyo",
                    "Tabou",
                ],
            },
            {
                "name": "Cavally",
                "code": "CAV",
                "cities": [
                    "Guiglo",
                    "Toulepleu",
                    "Bloléquin",
                    "Taï",
                    "Zagné",
                ],
            },
            {
                "name": "Comoé",
                "code": "COM",
                "cities": [
                    "Abengourou",
                    "Agnibilékrou",
                    "Béttié",
                    "Maféré",
                    "Zaranou",
                    "Bocanda",
                ],
            },
            {
                "name": "Gboklé",
                "code": "GBOK",
                "cities": [
                    "Grand-Bassam",
                    "Bonoua",
                    "Ono",
                    "Noé",
                ],
            },
            {
                "name": "Gbêkê",
                "code": "GBEKE",
                "cities": [
                    "Bouaké",
                    "Sakassou",
                    "Botro",
                    "Kouassi-Kouassikro",
                    "Béoumi",
                ],
            },
            {
                "name": "Gbôklé",
                "code": "GBOKLE",
                "cities": [
                    "Abengourou",
                    "Bécédi-Brignan",
                    "Grand-Morié",
                ],
            },
            {
                "name": "Guémon",
                "code": "GUEM",
                "cities": [
                    "Man",
                    "Danané",
                    "Sipilou",
                    "Kouibly",
                    "Fengolo",
                    "Gbangbégouiné",
                    "Béoué",
                    "Tai",
                ],
            },
            {
                "name": "Hambol",
                "code": "HAM",
                "cities": [
                    "Katiola",
                    "Niakara",
                    "Ferkessédougou",
                    "Kobénan",
                ],
            },
            {
                "name": "Haut-Sassandra",
                "code": "HSAS",
                "cities": [
                    "Daloa",
                    "Vavoua",
                    "Haut-Sassandra",
                    "Issia",
                    "Gueyo",
                ],
            },
            {
                "name": "Iffou",
                "code": "IFF",
                "cities": [
                    "Daoukro",
                    "M'Bahiakro",
                    "Ananda",
                    "Azaguie",
                ],
            },
            {
                "name": "Indénié-Djuablin",
                "code": "IND",
                "cities": [
                    "Abengourou",
                    "Ano-Sud",
                    "Kossou",
                    "Arrah",
                ],
            },
            {
                "name": "Kabadougou",
                "code": "KAB",
                "cities": [
                    "Odienné",
                    "Samatiguila",
                    "Mankono",
                ],
            },
            {
                "name": "Lagunes",
                "code": "LAG",
                "cities": [
                    "Dabou",
                    "Jacqueville",
                    "Tiassalé",
                    "Alépé",
                    "Agboville",
                    "Grand-Bassam",
                ],
            },
            {
                "name": "Lacs",
                "code": "LAC",
                "cities": [
                    "Dimbokro",
                    "Bocanda",
                    "Yamoussoukro",
                    "Tiébissou",
                    "Toumodi",
                ],
            },
            {
                "name": "Marahoué",
                "code": "MAR",
                "cities": [
                    "Bouaflé",
                    "Sinfra",
                    "Zuéénoula",
                ],
            },
            {
                "name": "Mé",
                "code": "ME",
                "cities": [
                    "Adzopé",
                    "Akébé",
                    "Alépé",
                    "Attobrou",
                    "Bocanda",
                ],
            },
            {
                "name": "Moronou",
                "code": "MOR",
                "cities": [
                    "Bongouanou",
                    "Arrah",
                    "M'Bahiakro",
                ],
            },
            {
                "name": "Nawa",
                "code": "NAW",
                "cities": [
                    "Soubré",
                    "Buyo",
                    "Guéyo",
                    "Méagui",
                ],
            },
            {
                "name": "N'Zi",
                "code": "N'ZI",
                "cities": [
                    "Dimbokro",
                    "Kouassi-Kouassikro",
                    "Prikro",
                ],
            },
            {
                "name": "Poro",
                "code": "POR",
                "cities": [
                    "Korhogo",
                    "Ferkessédougou",
                    "Dikodougou",
                    "Niakara",
                ],
            },
            {
                "name": "San-Pédro",
                "code": "SANP",
                "cities": [
                    "San-Pédro",
                    "Tabou",
                    "Sassandra",
                ],
            },
            {
                "name": "Sud-Comoé",
                "code": "SUDC",
                "cities": [
                    "Abengourou",
                    "Ano-Sud",
                    "Bettie",
                    "Agnibilékrou",
                ],
            },
            {
                "name": "Sud-Tchologo",
                "code": "SUDT",
                "cities": [
                    "Ferkessédougou",
                    "Kong",
                    "Napié",
                ],
            },
            {
                "name": "Tchologo",
                "code": "TCHOL",
                "cities": [
                    "Ferkessédougou",
                    "Ouangolodougou",
                    "Napie",
                ],
            },
            {
                "name": "Tonkpi",
                "code": "TON",
                "cities": [
                    "Man",
                    "Danané",
                    "Sipilou",
                    "Zouan-Hounien",
                ],
            },
            {
                "name": "Worodougou",
                "code": "WOR",
                "cities": [
                    "Séguéla",
                    "Mankono",
                    "Kani",
                ],
            },
            {
                "name": "Yamoussoukro",
                "code": "YAM",
                "cities": [
                    "Yamoussoukro",
                    "Attiégouakro",
                    "Lolobo",
                ],
            },
            {
                "name": "Yopougon",
                "code": "YOP",
                "cities": [
                    "Yopougon",
                    "Anyama",
                    "Songon",
                ],
            },
            {
                "name": "Zanzan",
                "code": "ZAN",
                "cities": [
                    "Bondoukou",
                    "Tanda",
                    "Sakassou",
                    "Bouna",
                ],
            },
        ]

        # Créer les régions et villes
        regions_created = 0
        cities_created = 0

        for region_data in regions_data:
            region, created = Region.objects.get_or_create(
                name=region_data["name"],
                defaults={"code": region_data.get("code", ""), "is_active": True},
            )

            if created:
                regions_created += 1
                self.stdout.write(f"  + Region creee: {region.name}")
            else:
                self.stdout.write(f"  - Region existe deja: {region.name}")

            # Créer les villes de cette région
            for city_name in region_data.get("cities", []):
                city, created = City.objects.get_or_create(
                    name=city_name,
                    region=region,
                    defaults={"is_active": True},
                )

                if created:
                    cities_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTermine! "
                f"{regions_created} regions creees, "
                f"{cities_created} villes creees."
            )
        )
