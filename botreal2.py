import os
import json
import time
import random
import logging
from datetime import datetime
from telethon import TelegramClient, events, Button
from instagrapi import Client as InstagramClient
from colorama import init, Fore, Style
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import asyncio
import random
from typing import List, Dict
import getpass

# Initialisation
init()
load_dotenv()

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
        # Vitesse de frappe moyenne: 40 mots par minute
        words = len(text.split())
        return (words / 40) * 60 + random.uniform(0.5, 1.5)

    @staticmethod
    def get_scroll_delay() -> float:
        """Simule le temps de défilement humain"""
        return random.uniform(0.8, 2.0)

    @staticmethod
    def get_reading_delay(text: str) -> float:
        """Simule le temps de lecture humain"""
        # Vitesse de lecture moyenne: 200 mots par minute
        words = len(text.split())
        return (words / 200) * 60 + random.uniform(1.0, 3.0)

class ConfigManager:
    def __init__(self):
        self.config_file = 'config/api_config.json'
        self.accounts_file = 'config/telegram_accounts.json'
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
        print(f"\n{Fore.CYAN}=== Configuration API Telegram ==={Style.RESET_ALL}")
        
        if 'api_id' not in self.config or 'api_hash' not in self.config:
            print("Configuration API non trouvée. Veuillez entrer vos credentials:")
            api_id = input("API ID: ").strip()
            api_hash = input("API Hash: ").strip()
            
            self.config['api_id'] = api_id
            self.config['api_hash'] = api_hash
            self.save_config()
            print(f"{Fore.GREEN}✓ Configuration API sauvegardée{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}✓ Configuration API trouvée{Style.RESET_ALL}")
            print(f"API ID: {self.config['api_id']}")
            print(f"API Hash: {self.config['api_hash']}")
            
            change = input("\nVoulez-vous modifier la configuration? (o/n): ").lower()
            if change == 'o':
                api_id = input("Nouvel API ID: ").strip()
                api_hash = input("Nouvel API Hash: ").strip()
                
                self.config['api_id'] = api_id
                self.config['api_hash'] = api_hash
                self.save_config()
                print(f"{Fore.GREEN}✓ Configuration API mise à jour{Style.RESET_ALL}")

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

    def add_telegram_account(self, phone: str, session_name: str):
        """Ajoute un compte Telegram"""
        try:
            # Vérifier si le compte existe déjà
            if phone in self.accounts:
                print(f"{Fore.YELLOW}⚠️ Ce compte existe déjà{Style.RESET_ALL}")
                return False

            # Ajouter le compte
            self.accounts[phone] = {
                'session': session_name,
                'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_accounts()
            print(f"{Fore.GREEN}✓ Compte ajouté avec succès{Style.RESET_ALL}")
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
                print(f"{Fore.GREEN}✓ Compte supprimé avec succès{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}⚠️ Compte non trouvé{Style.RESET_ALL}")
                return False
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du compte: {e}")
            return False

    def list_accounts(self):
        """Liste tous les comptes enregistrés"""
        if not self.accounts:
            print(f"{Fore.YELLOW}Aucun compte enregistré{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}=== Comptes Telegram enregistrés ==={Style.RESET_ALL}")
        for phone, data in self.accounts.items():
            print(f"\nNuméro: {phone}")
            print(f"Session: {data['session']}")
            print(f"Ajouté le: {data['added_date']}")

class SMMBot:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.account_manager = AccountManager()
        self.telegram_accounts = {}
        self.instagram_accounts = {}
        self.current_telegram_account = None
        self.current_instagram_account = None
        self.smm_bot_username = "@SmmKingdomTasksBot"
        self.task_count = 0
        self.instagram_accounts_index = 0
        self.human_behavior = HumanBehavior()
        
        # Chargement des comptes existants
        self.load_accounts()

    def verify_telegram_bot_connection(self, client):
        """Vérifie si le compte Telegram est connecté au bot SMM"""
        try:
            # Vérifier si le bot est dans les contacts
            entity = client.get_entity(self.smm_bot_username)
            if entity:
                logging.info(f"Compte Telegram connecté au bot {self.smm_bot_username}")
                return True
            return False
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de la connexion au bot: {e}")
            return False

    async def simulate_human_interaction(self, client, message, button_text: str = None):
        """Simule une interaction humaine avec des délais et des mouvements"""
        try:
            # Simuler le temps de lecture du message
            await asyncio.sleep(self.human_behavior.get_reading_delay(message.text))
            
            if button_text:
                # Simuler le temps de réflexion avant de cliquer
                await asyncio.sleep(self.human_behavior.get_random_delay(0.5, 1.5))
                
                # Simuler le mouvement de la souris
                await asyncio.sleep(self.human_behavior.get_random_delay(0.3, 0.7))
                
                # Cliquer sur le bouton
                await message.click(text=button_text)
                
                # Simuler le temps de réaction après le clic
                await asyncio.sleep(self.human_behavior.get_random_delay(0.8, 1.5))
        except Exception as e:
            logging.error(f"Erreur lors de la simulation d'interaction: {e}")

    async def verify_instagram_account(self, client, instagram_username):
        """Vérifie si le compte Instagram est dans la liste des comptes du bot et exécute les tâches"""
        try:
            # Envoyer /start avec un délai de frappe humain
            await client.send_message(self.smm_bot_username, '/start')
            await asyncio.sleep(self.human_behavior.get_typing_delay('/start'))
            
            # Attendre la réponse du bot
            await asyncio.sleep(self.human_behavior.get_random_delay(1.5, 3.0))
            
            # Cliquer sur le bouton Tasks avec comportement humain
            async for message in client.iter_messages(self.smm_bot_username, limit=1):
                if message.buttons:
                    for row in message.buttons:
                        for button in row:
                            if 'Tasks' in button.text:
                                await self.simulate_human_interaction(client, message, button.text)
                                logging.info("✅ Bouton 'Tasks' cliqué")
                                break
            
            # Simuler le défilement et la lecture
            await asyncio.sleep(self.human_behavior.get_scroll_delay())
            
            # Cliquer sur Instagram avec comportement humain
            async for message in client.iter_messages(self.smm_bot_username, limit=1):
                if message.buttons:
                    for row in message.buttons:
                        for button in row:
                            if 'Instagram' in button.text:
                                await self.simulate_human_interaction(client, message, button.text)
                                logging.info("✅ Bouton 'Instagram' cliqué")
                                break
            
            # Simuler le temps de chargement de la liste
            await asyncio.sleep(self.human_behavior.get_random_delay(2.0, 4.0))
            
            # Vérifier la liste des tâches et exécuter
            async for message in client.iter_messages(self.smm_bot_username, limit=1):
                if message.buttons:
                    for row in message.buttons:
                        for button in row:
                            if instagram_username.lower() in button.text.lower():
                                # Simuler la lecture de la liste
                                await asyncio.sleep(self.human_behavior.get_reading_delay(message.text))
                                
                                # Simuler la recherche du compte
                                await asyncio.sleep(self.human_behavior.get_random_delay(1.0, 2.0))
                                
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
        """Démarre le bot"""
        if not self.telegram_accounts or not self.instagram_accounts:
            logging.error("Aucun compte configuré")
            return

        try:
            # Connexion au premier compte Telegram
            first_phone = list(self.telegram_accounts.keys())[0]
            account = self.telegram_accounts[first_phone]
            client = TelegramClient(
                account['session'],
                account['api_id'],
                account['api_hash']
            )
            
            # Vérifier la connexion au bot
            if not self.verify_telegram_bot_connection(client):
                logging.error(f"Le compte Telegram n'est pas connecté au bot {self.smm_bot_username}")
                return

            @client.on(events.NewMessage(from_users=self.smm_bot_username))
            async def handle_new_message(event):
                message = event.message.text
                task = self.parse_task_message(message)
                
                if task:
                    # Obtenir le prochain compte Instagram
                    instagram_account = self.get_next_instagram_account()
                    if not instagram_account:
                        logging.error("Aucun compte Instagram disponible")
                        return

                    # Vérifier si le compte Instagram est dans la liste du bot
                    if not await self.verify_instagram_account(client, instagram_account):
                        logging.warning(f"Compte Instagram {instagram_account} non trouvé dans la liste du bot")
                        return

                    # Exécuter la tâche
                    if self.execute_instagram_task(task):
                        logging.info(f"Tâche exécutée avec succès pour le compte {instagram_account}")
                        # Attente aléatoire entre les actions
                        time.sleep(random.randint(30, 60))
                    else:
                        logging.error(f"Échec de l'exécution de la tâche pour le compte {instagram_account}")

            await client.start()
            await client.run_until_disconnected()
            
        except Exception as e:
            logging.error(f"Erreur lors du démarrage du bot: {e}")

    async def execute_instagram_task(self, task):
        """Exécute une tâche Instagram avec comportement humain"""
        try:
            if not self.current_instagram_account:
                logging.error("❌ Aucun compte Instagram actif")
                return False

            # Simuler le temps de réflexion avant d'exécuter la tâche
            await asyncio.sleep(self.human_behavior.get_random_delay(2.0, 4.0))
            
            # Exécuter la tâche selon son type avec des délais humains
            if task['type'] == 'follow':
                await asyncio.sleep(self.human_behavior.get_random_delay(1.5, 3.0))
                logging.info(f"✅ Tâche de follow exécutée pour {task['target']}")
            elif task['type'] == 'like':
                await asyncio.sleep(self.human_behavior.get_random_delay(1.0, 2.5))
                logging.info(f"✅ Tâche de like exécutée pour {task['target']}")
            elif task['type'] == 'comment':
                # Simuler le temps de rédaction du commentaire
                await asyncio.sleep(self.human_behavior.get_typing_delay(task.get('comment', '')))
                logging.info(f"✅ Tâche de commentaire exécutée pour {task['target']}")
            
            # Simuler le temps de vérification après l'action
            await asyncio.sleep(self.human_behavior.get_random_delay(1.0, 2.0))
            return True
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'exécution de la tâche: {e}")
            return False

    def setup_telegram_account(self):
        """Configure un nouveau compte Telegram"""
        print(f"\n{Fore.CYAN}=== Configuration d'un compte Telegram ==={Style.RESET_ALL}")
        
        # Obtenir les credentials API
        api_id, api_hash = self.config_manager.get_api_credentials()
        
        # Demander le numéro de téléphone
        phone = input("\nNuméro de téléphone (format international, ex: +33612345678): ").strip()
        
        # Générer un nom de session unique
        session_name = f"accounts/telegram/session_{phone.replace('+', '')}"
        
        try:
            # Créer le client Telegram
            client = TelegramClient(session_name, api_id, api_hash)
            
            # Démarrer le client
            client.start(phone)
            
            # Ajouter le compte
            if self.account_manager.add_telegram_account(phone, session_name):
                print(f"{Fore.GREEN}✓ Compte configuré avec succès{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Erreur lors de la configuration du compte{Style.RESET_ALL}")
            
            # Déconnecter le client
            client.disconnect()
            
        except Exception as e:
            logging.error(f"Erreur lors de la configuration du compte: {e}")
            print(f"{Fore.RED}✗ Erreur lors de la configuration du compte{Style.RESET_ALL}")

def main_menu():
    """Menu principal du bot"""
    bot = SMMBot()
    
    while True:
        print(f"\n{Fore.CYAN}=== Menu Principal ==={Style.RESET_ALL}")
        print("1. Démarrer le bot")
        print("2. Configurer un compte Telegram")
        print("3. Gérer les comptes Telegram")
        print("4. Ajouter un compte Instagram")
        print("5. Voir les comptes enregistrés")
        print("6. Quitter")
        
        choice = input("\nVotre choix: ")
        
        if choice == "1":
            import asyncio
            asyncio.run(bot.start_bot())
        elif choice == "2":
            bot.setup_telegram_account()
        elif choice == "3":
            print(f"\n{Fore.CYAN}=== Gestion des comptes Telegram ==={Style.RESET_ALL}")
            print("1. Voir les comptes")
            print("2. Supprimer un compte")
            subchoice = input("\nVotre choix: ")
            
            if subchoice == "1":
                bot.account_manager.list_accounts()
            elif subchoice == "2":
                phone = input("Numéro de téléphone à supprimer: ").strip()
                bot.account_manager.remove_telegram_account(phone)
        elif choice == "4":
            username = input("Nom d'utilisateur Instagram: ")
            password = getpass.getpass("Mot de passe Instagram: ")
            bot.add_instagram_account(username, password)
        elif choice == "5":
            print("\nComptes Telegram:", list(bot.telegram_accounts.keys()))
            print("Comptes Instagram:", list(bot.instagram_accounts.keys()))
        elif choice == "6":
            break
        else:
            print("Choix invalide")

if __name__ == "__main__":
    main_menu() 