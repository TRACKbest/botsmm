import os
import json
import time
import random
import logging
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.tl.types import User
from instagrapi import Client as InstagramClient
from colorama import init, Fore, Style
import asyncio
import getpass
import re
from typing import List, Dict

# Initialisation
init()

# Création des dossiers nécessaires
os.makedirs('logs', exist_ok=True)
os.makedirs('accounts/telegram', exist_ok=True)
os.makedirs('accounts/instagram', exist_ok=True)
os.makedirs('config', exist_ok=True)

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/{datetime.now().strftime("%Y-%m-%d")}.txt'),
        logging.StreamHandler()
    ]
)

class HumanBehavior:
    @staticmethod
    def get_random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> float:
        """Retourne un délai aléatoire pour simuler le comportement humain"""
        return random.uniform(min_seconds, max_seconds)

    @staticmethod
    def get_typing_delay(text: str) -> float:
        """Simule le temps de frappe humain"""
        words = len(text.split())
        return (words / 40) * 60 + random.uniform(0.5, 2.0)

    @staticmethod
    def get_scroll_delay() -> float:
        """Simule le temps de défilement humain"""
        return random.uniform(0.8, 2.5)

    @staticmethod
    def get_reading_delay(text: str) -> float:
        """Simule le temps de lecture humain"""
        words = len(text.split())
        return (words / 200) * 60 + random.uniform(1.0, 4.0)

class ConfigManager:
    def __init__(self):
        self.config_file = 'config/api_config.json'
        self.load_config()

    def load_config(self):
        """Charge la configuration depuis le fichier"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {}
        except Exception as e:
            logging.error(f"Erreur lors du chargement de la configuration: {e}")
            self.config = {}

    def save_config(self):
        """Sauvegarde la configuration dans le fichier"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde de la configuration: {e}")

    def get_api_credentials(self):
        """Demande et stocke les credentials API"""
        print(f"\n{Fore.CYAN}=== Configuration des identifiants API Telegram ==={Style.RESET_ALL}")
        
        if 'api_id' not in self.config or 'api_hash' not in self.config:
            print("Aucune configuration API trouvée. Entrons les informations !")
            api_id = input("Entrez votre API ID : ").strip()
            api_hash = input("Entrez votre API Hash : ").strip()
            
            self.config['api_id'] = api_id
            self.config['api_hash'] = api_hash
            self.save_config()
            print(f"{Fore.GREEN}✓ Configuration API enregistrée avec succès !{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}✓ Configuration API déjà présente !{Style.RESET_ALL}")
            print(f"API ID : {self.config['api_id']}")
            print(f"API Hash : {self.config['api_hash'][:8]}... (caché pour sécurité)")
            
            change = input("\nVoulez-vous modifier ces identifiants ? (o/n) : ").lower()
            if change == 'o':
                api_id = input("Nouvel API ID : ").strip()
                api_hash = input("Nouvel API Hash : ").strip()
                
                self.config['api_id'] = api_id
                self.config['api_hash'] = api_hash
                self.save_config()
                print(f"{Fore.GREEN}✓ Configuration API mise à jour !{Style.RESET_ALL}")

        return self.config['api_id'], self.config['api_hash']

class AccountManager:
    def __init__(self):
        self.accounts_file = 'config/telegram_accounts.json'
        self.load_accounts()

    def load_accounts(self):
        """Charge les comptes depuis le fichier"""
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'r') as f:
                    self.accounts = json.load(f)
            else:
                self.accounts = {}
        except Exception as e:
            logging.error(f"Erreur lors du chargement des comptes: {e}")
            self.accounts = {}

    def save_accounts(self):
        """Sauvegarde les comptes dans le fichier"""
        try:
            with open(self.accounts_file, 'w') as f:
                json.dump(self.accounts, f, indent=4)
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des comptes: {e}")

    async def validate_telegram_account(self, phone: str, api_id: str, api_hash: str, session_name: str) -> bool:
        """Valide un compte Telegram en vérifiant la connexion et l'accès au bot"""
        try:
            client = TelegramClient(session_name, api_id, api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone)
                code = input(f"Entrez le code reçu pour {phone} : ")
                try:
                    await client.sign_in(phone, code)
                except Exception as e:
                    print(f"{Fore.RED}✗ Erreur lors de la connexion : {str(e)}{Style.RESET_ALL}")
                    await client.disconnect()
                    return False
            
            # Vérifier la connexion au bot
            bot_username = "@SmmKingdomTasksBot"
            try:
                entity = await client.get_entity(bot_username)
                if isinstance(entity, User):
                    logging.info(f"Compte Telegram {phone} connecté au bot {bot_username}")
                    await client.disconnect()
                    return True
            except Exception as e:
                logging.error(f"Erreur lors de la connexion au bot {bot_username}: {e}")
                await client.disconnect()
                return False
        except Exception as e:
            logging.error(f"Erreur lors de la validation du compte Telegram {phone}: {e}")
            await client.disconnect()
            return False

    def add_telegram_account(self, phone: str, session_name: str, api_id: str, api_hash: str):
        """Ajoute un compte Telegram après validation"""
        try:
            if phone in self.accounts:
                print(f"{Fore.YELLOW}⚠️ Ce numéro est déjà enregistré !{Style.RESET_ALL}")
                return False

            self.accounts[phone] = {
                'session': session_name,
                'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'api_id': api_id,
                'api_hash': api_hash
            }
            self.save_accounts()
            print(f"{Fore.GREEN}✓ Compte Telegram ajouté avec succès !{Style.RESET_ALL}")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du compte: {e}")
            return False

    def remove_telegram_account(self, phone: str):
        """Supprime un compte Telegram"""
        try:
            if phone in self.accounts:
                del self.accounts[phone]
                self.save_accounts()
                print(f"{Fore.GREEN}✓ Compte supprimé avec succès !{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}⚠️ Ce numéro n'est pas enregistré !{Style.RESET_ALL}")
                return False
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du compte: {e}")
            return False

    def list_accounts(self):
        """Liste tous les comptes enregistrés"""
        if not self.accounts:
            print(f"{Fore.YELLOW}Aucun compte Telegram enregistré pour le moment.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}=== Comptes Telegram enregistrés ==={Style.RESET_ALL}")
        for phone, data in self.accounts.items():
            print(f"\nNuméro : {phone}")
            print(f"Session : {data['session']}")
            print(f"Ajouté le : {data['added_date']}")

class SMMBot:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.account_manager = AccountManager()
        self.telegram_account = None  # Un seul compte Telegram connecté
        self.instagram_accounts = {}
        self.current_instagram_account = None
        self.smm_bot_username = "@SmmKingdomTasksBot"
        self.task_count = 0
        self.instagram_accounts_index = 0
        self.human_behavior = HumanBehavior()
        self.load_accounts()

    def load_accounts(self):
        """Charge le compte Telegram connecté et les comptes Instagram"""
        try:
            instagram_accounts_file = 'config/instagram_accounts.json'
            if os.path.exists(instagram_accounts_file):
                with open(instagram_accounts_file, 'r') as f:
                    self.instagram_accounts = json.load(f)
            else:
                self.instagram_accounts = {}
            logging.info(f"Chargement réussi : {len(self.instagram_accounts)} comptes Instagram")
        except Exception as e:
            logging.error(f"Erreur lors du chargement des comptes: {e}")
            self.instagram_accounts = {}

    async def verify_telegram_bot_connection(self, client):
        """Vérifie si le compte Telegram est connecté au bot SMM"""
        try:
            entity = await client.get_entity(self.smm_bot_username)
            if isinstance(entity, User):
                logging.info(f"Compte Telegram connecté au bot {self.smm_bot_username}")
                return True
            return False
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de la connexion au bot: {e}")
            return False

    async def simulate_human_interaction(self, client, message, button_text: str = None):
        """Simule une interaction humaine avec des délais et des mouvements"""
        try:
            await asyncio.sleep(self.human_behavior.get_reading_delay(message.text))
            if button_text:
                await asyncio.sleep(self.human_behavior.get_random_delay(0.5, 2.0))
                await asyncio.sleep(self.human_behavior.get_random_delay(0.3, 0.8))
                await message.click(text=button_text)
                await asyncio.sleep(self.human_behavior.get_random_delay(0.8, 2.0))
        except Exception as e:
            logging.error(f"Erreur lors de la simulation d'interaction: {e}")

    async def verify_instagram_account(self, client, instagram_username):
        """Vérifie si le compte Instagram est dans la liste des comptes du bot et exécute les tâches"""
        try:
            await client.send_message(self.smm_bot_username, '/start')
            await asyncio.sleep(self.human_behavior.get_typing_delay('/start'))
            await asyncio.sleep(self.human_behavior.get_random_delay(1.5, 3.5))
            
            async for message in client.iter_messages(self.smm_bot_username, limit=1):
                if message.buttons:
                    for row in message.buttons:
                        for button in row:
                            if 'Tasks' in button.text:
                                await self.simulate_human_interaction(client, message, button.text)
                                logging.info("✅ Bouton 'Tasks' cliqué")
                                break
            
            await asyncio.sleep(self.human_behavior.get_scroll_delay())
            
            async for message in client.iter_messages(self.smm_bot_username, limit=1):
                if message.buttons:
                    for row in message.buttons:
                        for button in row:
                            if 'Instagram' in button.text:
                                await self.simulate_human_interaction(client, message, button.text)
                                logging.info("✅ Bouton 'Instagram' cliqué")
                                break
            
            await asyncio.sleep(self.human_behavior.get_random_delay(2.0, 5.0))
            
            async for message in client.iter_messages(self.smm_bot_username, limit=1):
                if message.buttons:
                    for row in message.buttons:
                        for button in row:
                            if instagram_username.lower() in button.text.lower():
                                await asyncio.sleep(self.human_behavior.get_reading_delay(message.text))
                                await asyncio.sleep(self.human_behavior.get_random_delay(1.0, 2.5))
                                await self.simulate_human_interaction(client, message, button.text)
                                logging.info(f"✅ Tâche lancée pour {instagram_username}")
                                return True
                if instagram_username.lower() in message.text.lower():
                    await asyncio.sleep(self.human_behavior.get_reading_delay(message.text))
                    logging.info(f"✅ Compte Instagram {instagram_username} trouvé dans la liste")
                    return True
            
            logging.warning(f"❌ Compte Instagram {instagram_username} non trouvé dans la liste")
            return False
        except Exception as e:
            logging.error(f"❌ Erreur lors de la vérification du compte Instagram: {e}")
            return False

    def get_next_instagram_account(self):
        """Obtient le prochain compte Instagram à utiliser"""
        if not self.instagram_accounts:
            return None
        
        accounts = list(self.instagram_accounts.keys())
        if self.instagram_accounts_index >= len(accounts):
            self.instagram_accounts_index = 0
            self.task_count += 1
            logging.info(f"Cycle de tâches terminé. Compteur: {self.task_count}")
        
        account = accounts[self.instagram_accounts_index]
        self.instagram_accounts_index += 1
        return account

    async def start_bot(self):
        """Démarre le bot avec le compte Telegram connecté"""
        if not self.telegram_account:
            print(f"{Fore.RED}✗ Erreur : Aucun compte Telegram connecté. Veuillez en configurer un d'abord.{Style.RESET_ALL}")
            return
        if not self.instagram_accounts:
            print(f"{Fore.RED}✗ Erreur : Aucun compte Instagram configuré. Veuillez en ajouter avant de démarrer.{Style.RESET_ALL}")
            return

        try:
            client = TelegramClient(
                self.telegram_account['session'],
                self.telegram_account['api_id'],
                self.telegram_account['api_hash']
            )
            
            await client.connect()
            if not await client.is_user_authorized():
                print(f"{Fore.RED}✗ Erreur : Le compte Telegram {self.telegram_account['phone']} n'est pas autorisé. Veuillez le reconfigurer.{Style.RESET_ALL}")
                await client.disconnect()
                return

            if not await self.verify_telegram_bot_connection(client):
                print(f"{Fore.RED}✗ Erreur : Impossible de se connecter au bot {self.smm_bot_username}. Vérifiez votre connexion ou le bot.{Style.RESET_ALL}")
                await client.disconnect()
                return

            @client.on(events.NewMessage(from_users=self.smm_bot_username))
            async def handle_new_message(event):
                message = event.message.text
                task = self.parse_task_message(message)
                
                if task:
                    instagram_account = self.get_next_instagram_account()
                    if not instagram_account:
                        logging.error("Aucun compte Instagram disponible")
                        return

                    if not await self.verify_instagram_account(client, instagram_account):
                        logging.warning(f"Compte Instagram {instagram_account} non trouvé dans la liste du bot")
                        return

                    if await self.execute_instagram_task(task):
                        logging.info(f"Tâche exécutée avec succès pour le compte {instagram_account}")
                        await asyncio.sleep(random.uniform(30, 60))
                    else:
                        logging.error(f"Échec de l'exécution de la tâche pour le compte {instagram_account}")

            print(f"{Fore.GREEN}✓ Bot démarré avec succès ! En attente de tâches...{Style.RESET_ALL}")
            await client.start()
            await client.run_until_disconnected()
            
        except Exception as e:
            logging.error(f"Erreur lors du démarrage du bot: {e}")
            print(f"{Fore.RED}✗ Erreur lors du démarrage du bot : {str(e)}{Style.RESET_ALL}")

    async def execute_instagram_task(self, task):
        """Exécute une tâche Instagram avec comportement humain"""
        try:
            if not self.current_instagram_account:
                logging.error("❌ Aucun compte Instagram actif")
                return False

            await asyncio.sleep(self.human_behavior.get_random_delay(2.0, 5.0))
            
            if task['type'] == 'follow':
                await asyncio.sleep(self.human_behavior.get_random_delay(1.5, 3.5))
                logging.info(f"✅ Tâche de follow exécutée pour {task['target']}")
            elif task['type'] == 'like':
                await asyncio.sleep(self.human_behavior.get_random_delay(1.0, 3.0))
                logging.info(f"✅ Tâche de like exécutée pour {task['target']}")
            elif task['type'] == 'comment':
                await asyncio.sleep(self.human_behavior.get_typing_delay(task.get('comment', '')))
                logging.info(f"✅ Tâche de commentaire exécutée pour {task['target']}")
            
            await asyncio.sleep(self.human_behavior.get_random_delay(1.0, 2.5))
            return True
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'exécution de la tâche: {e}")
            return False

    def parse_task_message(self, message: str) -> Dict:
        """Analyse le message pour extraire la tâche (implémentation factice)"""
        return {'type': 'follow', 'target': 'example_user'}

    async def setup_telegram_account(self):
        """Configure un nouveau compte Telegram avec validation"""
        print(f"\n{Fore.CYAN}=== Connexion d'un compte Telegram ==={Style.RESET_ALL}")
        
        api_id, api_hash = self.config_manager.get_api_credentials()
        
        phone = input("\nEntrez le numéro de téléphone (format international, ex: +33612345678) : ").strip()
        if not re.match(r'^\+\d{10,15}$', phone):
            print(f"{Fore.RED}✗ Erreur : Format de numéro invalide. Utilisez le format international (ex: +33612345678).{Style.RESET_ALL}")
            return

        session_name = f"accounts/telegram/session_{phone.replace('+', '')}"
        
        try:
            if await self.account_manager.validate_telegram_account(phone, api_id, api_hash, session_name):
                if self.account_manager.add_telegram_account(phone, session_name, api_id, api_hash):
                    self.telegram_account = {
                        'phone': phone,
                        'session': session_name,
                        'api_id': api_id,
                        'api_hash': api_hash
                    }
                    print(f"{Fore.GREEN}✓ Compte Telegram connecté avec succès !{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ Erreur lors de l'enregistrement du compte.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Erreur : Impossible de valider le compte Telegram ou de se connecter au bot.{Style.RESET_ALL}")
        except Exception as e:
            logging.error(f"Erreur lors de la configuration du compte: {e}")
            print(f"{Fore.RED}✗ Erreur lors de la configuration : {str(e)}{Style.RESET_ALL}")

    def add_instagram_account(self, username: str, password: str):
        """Ajoute un compte Instagram"""
        try:
            if username in self.instagram_accounts:
                print(f"{Fore.YELLOW}⚠️ Ce compte Instagram est déjà enregistré !{Style.RESET_ALL}")
                return False

            self.instagram_accounts[username] = {
                'password': password,
                'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            instagram_accounts_file = 'config/instagram_accounts.json'
            with open(instagram_accounts_file, 'w') as f:
                json.dump(self.instagram_accounts, f, indent=4)

            print(f"{Fore.GREEN}✓ Compte Instagram ajouté avec succès !{Style.RESET_ALL}")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du compte Instagram: {e}")
            print(f"{Fore.RED}✗ Erreur lors de l'ajout du compte Instagram : {str(e)}{Style.RESET_ALL}")
            return False

    def remove_instagram_account(self, username: str):
        """Supprime un compte Instagram"""
        try:
            if username in self.instagram_accounts:
                del self.instagram_accounts[username]
                instagram_accounts_file = 'config/instagram_accounts.json'
                with open(instagram_accounts_file, 'w') as f:
                    json.dump(self.instagram_accounts, f, indent=4)
                print(f"{Fore.GREEN}✓ Compte Instagram supprimé avec succès !{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}⚠️ Ce compte Instagram n'est pas enregistré !{Style.RESET_ALL}")
                return False
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du compte Instagram: {e}")
            return False

    def list_instagram_accounts(self):
        """Liste tous les comptes Instagram enregistrés"""
        if not self.instagram_accounts:
            print(f"{Fore.YELLOW}Aucun compte Instagram enregistré pour le moment.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}=== Comptes Instagram enregistrés ==={Style.RESET_ALL}")
        for username, data in self.instagram_accounts.items():
            print(f"\nNom d'utilisateur : {username}")
            print(f"Ajouté le : {data['added_date']}")

def main_menu():
    """Menu principal du bot"""
    bot = SMMBot()
    
    while True:
        print(f"\n{Fore.CYAN}=== Menu Principal ==={Style.RESET_ALL}")
        print("1. Démarrer le bot")
        print("2. Connecter un compte Telegram")
        print("3. Gérer les comptes Telegram")
        print("4. Gérer les comptes Instagram")
        print("5. Voir tous les comptes")
        print("6. Quitter")
        
        choice = input("\nVotre choix : ").strip()
        
        if choice == "1":
            asyncio.run(bot.start_bot())
        elif choice == "2":
            asyncio.run(bot.setup_telegram_account())
        elif choice == "3":
            print(f"\n{Fore.CYAN}=== Gestion des comptes Telegram ==={Style.RESET_ALL}")
            print("1. Voir les comptes")
            print("2. Supprimer un compte")
            subchoice = input("\nVotre choix : ").strip()
            
            if subchoice == "1":
                bot.account_manager.list_accounts()
            elif subchoice == "2":
                phone = input("Entrez le numéro de téléphone à supprimer : ").strip()
                bot.account_manager.remove_telegram_account(phone)
            else:
                print(f"{Fore.RED}Choix invalide. Retour au menu principal.{Style.RESET_ALL}")
        elif choice == "4":
            print(f"\n{Fore.CYAN}=== Gestion des comptes Instagram ==={Style.RESET_ALL}")
            print("1. Ajouter un compte")
            print("2. Voir les comptes")
            print("3. Supprimer un compte")
            subchoice = input("\nVotre choix : ").strip()
            
            if subchoice == "1":
                while True:
                    username = input("Nom d'utilisateur Instagram : ").strip()
                    password = getpass.getpass("Mot de passe Instagram : ")
                    bot.add_instagram_account(username, password)
                    choice = input("\nVoulez-vous ajouter un autre compte Instagram ? (o/n) : ").lower()
                    if choice != 'o':
                        break
            elif subchoice == "2":
                bot.list_instagram_accounts()
            elif subchoice == "3":
                username = input("Nom d'utilisateur à supprimer : ").strip()
                bot.remove_instagram_account(username)
            else:
                print(f"{Fore.RED}Choix invalide. Retour au menu principal.{Style.RESET_ALL}")
        elif choice == "5":
            print(f"\n{Fore.CYAN}=== Comptes enregistrés ==={Style.RESET_ALL}")
            print("\n=== Compte Telegram connecté ===")
            if bot.telegram_account:
                print(f"Numéro : {bot.telegram_account['phone']}")
                print(f"Session : {bot.telegram_account['session']}")
            else:
                print(f"{Fore.YELLOW}Aucun compte Telegram connecté.{Style.RESET_ALL}")
            print("\n=== Comptes Instagram ===")
            bot.list_instagram_accounts()
        elif choice == "6":
            print(f"{Fore.GREEN}À bientôt !{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Choix invalide. Veuillez choisir une option valide.{Style.RESET_ALL}")

if __name__ == "__main__":
    main_menu()