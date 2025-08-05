# -*- coding: utf-8 -*-
"""
Script de nettoyage des utilisateurs en doublon
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from collections import defaultdict
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Nettoie les utilisateurs en doublon basés sur l\'email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Effectue une simulation sans modifier la base de données',
        )
        parser.add_argument(
            '--auto-merge',
            action='store_true',
            help='Fusionne automatiquement les comptes sans demander confirmation',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_merge = options['auto_merge']

        self.stdout.write(
            self.style.SUCCESS('🔍 Analyse des utilisateurs en doublon...\n')
        )

        # Identifier les emails en doublon
        duplicates = self.find_duplicate_emails()

        if not duplicates:
            self.stdout.write(
                self.style.SUCCESS('✅ Aucun email en doublon trouvé!')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'⚠️  {len(duplicates)} emails en doublon trouvés:\n')
        )

        # Afficher les doublons
        for email, users in duplicates.items():
            self.display_duplicate_info(email, users)

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('\n🔍 Mode simulation - Aucune modification effectuée')
            )
            return

        # Confirmer avant de procéder
        if not auto_merge:
            confirm = input('\n❓ Voulez-vous procéder au nettoyage? (oui/non): ')
            if confirm.lower() not in ['oui', 'yes', 'y', 'o']:
                self.stdout.write('❌ Opération annulée')
                return

        # Nettoyer les doublons
        self.clean_duplicates(duplicates)

    def find_duplicate_emails(self):
        """Trouve tous les emails en doublon"""
        email_counts = defaultdict(list)

        # Grouper les utilisateurs par email
        for user in User.objects.all().select_related():
            if user.email:  # Ignorer les emails vides
                email_counts[user.email].append(user)

        # Garder seulement les emails avec plusieurs utilisateurs
        duplicates = {
            email: users for email, users in email_counts.items()
            if len(users) > 1
        }

        return duplicates

    def display_duplicate_info(self, email, users):
        """Affiche les informations sur les utilisateurs en doublon"""
        self.stdout.write(f'\n📧 Email: {email} ({len(users)} comptes)')
        self.stdout.write('─' * 60)

        for i, user in enumerate(users, 1):
            self.stdout.write(
                f'  {i}. ID: {user.id} | Username: {user.username} | '
                f'Inscrit: {user.date_joined.strftime("%d/%m/%Y %H:%M")} | '
                f'Actif: {"✅" if user.is_active else "❌"} | '
                f'Connexion: {user.last_login.strftime("%d/%m/%Y") if user.last_login else "Jamais"} | '
                f'Mot de passe: {"✅" if user.has_usable_password() else "🔒 Firebase"}'
            )

            # Afficher des infos supplémentaires
            if hasattr(user, 'first_name') and user.first_name:
                self.stdout.write(f'     Nom: {user.first_name} {user.last_name}')

    def clean_duplicates(self, duplicates):
        """Nettoie les utilisateurs en doublon"""
        cleaned_count = 0

        with transaction.atomic():
            for email, users in duplicates.items():
                self.stdout.write(f'\n🔧 Nettoyage de {email}...')

                # Stratégie de nettoyage
                primary_user = self.select_primary_user(users)
                duplicate_users = [u for u in users if u.id != primary_user.id]

                self.stdout.write(f'   Compte principal: {primary_user.username} (ID: {primary_user.id})')

                for dup_user in duplicate_users:
                    self.stdout.write(f'   Suppression: {dup_user.username} (ID: {dup_user.id})')

                    # Transférer les données importantes avant suppression
                    self.transfer_user_data(dup_user, primary_user)

                    # Supprimer l'utilisateur en doublon
                    dup_user.delete()
                    cleaned_count += 1

                self.stdout.write('   ✅ Nettoyage terminé')

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Nettoyage terminé! {cleaned_count} comptes en doublon supprimés.')
        )

    def select_primary_user(self, users):
        """Sélectionne l'utilisateur principal à conserver"""
        # Critères de priorité (du plus important au moins important):
        # 1. Utilisateur avec mot de passe utilisable (compte Django natif)
        # 2. Utilisateur actif
        # 3. Utilisateur avec la dernière connexion la plus récente
        # 4. Utilisateur inscrit le plus récemment

        # Trier par priorité
        def priority_score(user):
            score = 0

            # Préférer les comptes avec mot de passe (Django natif vs Firebase)
            if user.has_usable_password():
                score += 1000

            # Préférer les comptes actifs
            if user.is_active:
                score += 100

            # Préférer les comptes avec connexion récente
            if user.last_login:
                days_since_login = (timezone.now() - user.last_login).days
                score += max(0, 50 - days_since_login)  # Plus récent = score plus élevé

            # Préférer les comptes récents
            days_since_join = (timezone.now() - user.date_joined).days
            score += max(0, 10 - (days_since_join // 30))  # Plus récent = score plus élevé

            return score

        # Sélectionner l'utilisateur avec le score le plus élevé
        primary_user = max(users, key=priority_score)
        return primary_user

    def transfer_user_data(self, from_user, to_user):
        """Transfère les données importantes de l'ancien compte vers le principal"""
        try:
            # Transférer les commandes si applicable
            if hasattr(from_user, 'orders'):
                from_user.orders.update(user=to_user)

            # Transférer d'autres données liées si nécessaire
            # (Ajoutez ici d'autres modèles liés à l'utilisateur)

            # Mettre à jour les informations du compte principal si nécessaire
            if not to_user.first_name and from_user.first_name:
                to_user.first_name = from_user.first_name
            if not to_user.last_name and from_user.last_name:
                to_user.last_name = from_user.last_name

            # Garder la date de connexion la plus récente
            if from_user.last_login and (not to_user.last_login or from_user.last_login > to_user.last_login):
                to_user.last_login = from_user.last_login

            to_user.save()

        except Exception as e:
            logger.error(f'Erreur lors du transfert de données pour {from_user.username}: {e}')
