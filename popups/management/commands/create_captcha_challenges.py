"""
Commande pour créer des défis captcha simples et abordables
"""
import random

from django.core.management.base import BaseCommand

from popups.models import CaptchaChallenge


class Command(BaseCommand):
    help = "Créer des défis captcha simples et abordables"

    def handle(self, *args, **options):
        # Supprimer les anciens défis
        CaptchaChallenge.objects.all().delete()

        # Défis mathématiques simples
        math_challenges = [
            ("Combien font 2 + 3 ?", "5"),
            ("Combien font 7 - 4 ?", "3"),
            ("Combien font 3 × 2 ?", "6"),
            ("Combien font 8 ÷ 2 ?", "4"),
            ("Combien font 1 + 1 ?", "2"),
            ("Combien font 5 + 5 ?", "10"),
            ("Combien font 6 - 2 ?", "4"),
            ("Combien font 4 × 2 ?", "8"),
            ("Combien font 9 ÷ 3 ?", "3"),
            ("Combien font 3 + 7 ?", "10"),
        ]

        for question, answer in math_challenges:
            CaptchaChallenge.objects.create(
                challenge_type="math",
                question=question,
                answer=answer,
                difficulty="easy",
                is_active=True,
            )

        # Défis de texte simples
        text_challenges = [
            ("Écrivez le mot 'chat' en minuscules", "chat"),
            ("Écrivez le mot 'chien' en minuscules", "chien"),
            ("Écrivez le mot 'maison' en minuscules", "maison"),
            ("Écrivez le mot 'voiture' en minuscules", "voiture"),
            ("Écrivez le mot 'livre' en minuscules", "livre"),
            ("Écrivez le mot 'table' en minuscules", "table"),
            ("Écrivez le mot 'fleur' en minuscules", "fleur"),
            ("Écrivez le mot 'soleil' en minuscules", "soleil"),
            ("Écrivez le mot 'lune' en minuscules", "lune"),
            ("Écrivez le mot 'étoile' en minuscules", "étoile"),
        ]

        for question, answer in text_challenges:
            CaptchaChallenge.objects.create(
                challenge_type="text",
                question=question,
                answer=answer,
                difficulty="easy",
                is_active=True,
            )

        # Défis de sélection d'image simples
        image_challenges = [
            ("Sélectionnez l'animal", ["Chat", "Voiture", "Maison", "Livre"], "Chat"),
            ("Sélectionnez le fruit", ["Pomme", "Voiture", "Livre", "Table"], "Pomme"),
            (
                "Sélectionnez la couleur",
                ["Rouge", "Voiture", "Livre", "Table"],
                "Rouge",
            ),
            (
                "Sélectionnez l'objet rond",
                ["Ballon", "Livre", "Table", "Voiture"],
                "Ballon",
            ),
            (
                "Sélectionnez le véhicule",
                ["Voiture", "Pomme", "Livre", "Table"],
                "Voiture",
            ),
        ]

        for question, options, answer in image_challenges:
            CaptchaChallenge.objects.create(
                challenge_type="image",
                question=question,
                answer=answer,
                options=options,
                difficulty="easy",
                is_active=True,
            )

        # Défis checkbox simples
        checkbox_challenges = [
            (
                "Cochez la case si vous n'êtes pas un robot",
                ["Je ne suis pas un robot"],
                "Je ne suis pas un robot",
            ),
            (
                "Cochez la case si vous êtes humain",
                ["Je suis humain"],
                "Je suis humain",
            ),
            (
                "Cochez la case pour continuer",
                ["Je veux continuer"],
                "Je veux continuer",
            ),
        ]

        for question, options, answer in checkbox_challenges:
            CaptchaChallenge.objects.create(
                challenge_type="checkbox",
                question=question,
                answer=answer,
                options=options,
                difficulty="easy",
                is_active=True,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Créé {len(math_challenges) + len(text_challenges) + len(image_challenges) + len(checkbox_challenges)} défis captcha simples"
            )
        )
