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

# Initialisation
init()
load_dotenv()

# Création des dossiers nécessaires
os.makedirs('logs', exist_ok=True)
os.makedirs('accounts/telegram', exist_ok=True)
os.makedirs('accounts/instagram', exist_ok=True)

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/{datetime.now().strftime("%Y-%m-%d")}.txt'),
        logging.StreamHandler()
    ]
)

class SMMBot:
    def __init__(self):
        self.telegram_accounts = {}
        self.instagram_accounts = {}
        self.current_telegram_account = None
        self.current_instagram_account = None
        self.smm_bot_username = "@SmmKingdomTasksBot"
        self.task_count = 0
        self.instagram_accounts_index = 0
        
        # Chargement des comptes existants
        self.load_accounts()

    def load_accounts(self):
        """Charge les comptes depuis les fichiers de configuration"""
        try:
            # Charger les comptes Telegram
            telegram_accounts_file = 'accounts/telegram/accounts.json'
            if os.path.exists(telegram_accounts_file):
                with open(telegram_accounts_file, 'r') as f:
                    self.telegram_accounts = json.load(f)
                logging.info(f"Comptes Telegram chargés: {len(self.telegram_accounts)} comptes")

            # Charger les comptes Instagram
            instagram_accounts_file = 'accounts/instagram/accounts.json'
            if os.path.exists(instagram_accounts_file):
                with open(instagram_accounts_file, 'r') as f:
                    self.instagram_accounts = json.load(f)
                logging.info(f"Comptes Instagram chargés: {len(self.instagram_accounts)} comptes")

        except Exception as e:
            logging.error(f"Erreur lors du chargement des comptes: {e}")
            # Initialiser avec des dictionnaires vides en cas d'erreur
            self.telegram_accounts = {}
            self.instagram_accounts = {}

    def save_accounts(self):
        """Sauvegarde les comptes dans les fichiers de configuration"""
        try:
            # Sauvegarder les comptes Telegram
            os.makedirs('accounts/telegram', exist_ok=True)
            with open('accounts/telegram/accounts.json', 'w') as f:
                json.dump(self.telegram_accounts, f, indent=4)
            logging.info("Comptes Telegram sauvegardés")

            # Sauvegarder les comptes Instagram
            os.makedirs('accounts/instagram', exist_ok=True)
            with open('accounts/instagram/accounts.json', 'w') as f:
                json.dump(self.instagram_accounts, f, indent=4)
            logging.info("Comptes Instagram sauvegardés")

        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des comptes: {e}")

    def add_instagram_account(self, username, password):
        """Ajoute un compte Instagram"""
        try:
            print(f"\n{Fore.YELLOW}Tentative de connexion au compte Instagram {username}...{Style.RESET_ALL}")
            
            # Créer une instance du client Instagram
            cl = InstagramClient()
            
            # Tenter la connexion
            cl.login(username, password)
            
            # Si la connexion réussit, sauvegarder les informations
            self.instagram_accounts[username] = {
                'username': username,
                'password': password,
                'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Sauvegarder les comptes
            self.save_accounts()
            
            print(f"{Fore.GREEN}Compte Instagram {username} ajouté avec succès !{Style.RESET_ALL}")
            logging.info(f"Compte Instagram {username} ajouté avec succès")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}Erreur lors de l'ajout du compte Instagram: {str(e)}{Style.RESET_ALL}")
            logging.error(f"Erreur lors de l'ajout du compte Instagram {username}: {e}")
            return False

    def add_telegram_account(self, phone):
        """Ajoute un compte Telegram"""
        try:
            print(f"\n{Fore.YELLOW}Tentative de connexion au compte Telegram {phone}...{Style.RESET_ALL}")
            
            # Demander les identifiants API à l'utilisateur
            print("\nVeuillez entrer vos identifiants Telegram API :")
            api_id = input("API ID: ")
            api_hash = input("API HASH: ")
            
            # Vérifier que les identifiants ne sont pas vides
            if not api_id or not api_hash:
                print(f"{Fore.RED}Les identifiants API sont requis.{Style.RESET_ALL}")
                return False
            
            # Créer le client Telegram
            client = TelegramClient(f'accounts/telegram/{phone}', 
                                  api_id, 
                                  api_hash)
            
            # Connexion et envoi du code
            client.connect()
            if not client.is_user_authorized():
                client.send_code_request(phone)
                print(f"{Fore.YELLOW}Un code de confirmation a été envoyé sur votre compte Telegram {phone}{Style.RESET_ALL}")
                code = input('Entrez le code reçu: ')
                try:
                    client.sign_in(phone, code)
                except Exception as e:
                    if "2FA" in str(e):
                        print(f"{Fore.YELLOW}Ce compte nécessite une authentification à deux facteurs.{Style.RESET_ALL}")
                        password = input("Entrez votre mot de passe 2FA: ")
                        client.sign_in(password=password)
                    else:
                        raise e
            
            # Sauvegarder les informations du compte
            self.telegram_accounts[phone] = {
                'phone': phone,
                'session': f'accounts/telegram/{phone}.session',
                'api_id': api_id,
                'api_hash': api_hash,
                'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Sauvegarder les comptes
            self.save_accounts()
            
            print(f"{Fore.GREEN}Compte Telegram {phone} ajouté avec succès !{Style.RESET_ALL}")
            logging.info(f"Compte Telegram {phone} ajouté avec succès")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}Erreur lors de l'ajout du compte Telegram: {str(e)}{Style.RESET_ALL}")
            logging.error(f"Erreur lors de l'ajout du compte Telegram {phone}: {e}")
            return False

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

    async def verify_instagram_account(self, client, instagram_username):
        """Vérifie si le compte Instagram est dans la liste des comptes du bot"""
        try:
            # Envoyer /start pour obtenir le menu principal
            await client.send_message(self.smm_bot_username, '/start')
            time.sleep(2)
            
            # Cliquer sur le bouton Tasks
            async for message in client.iter_messages(self.smm_bot_username, limit=1):
                if message.buttons:
                    for row in message.buttons:
                        for button in row:
                            if 'Tasks' in button.text:
                                await message.click(data=button.data)
                                break
            
            time.sleep(2)
            
            # Cliquer sur Instagram
            async for message in client.iter_messages(self.smm_bot_username, limit=1):
                if message.buttons:
                    for row in message.buttons:
                        for button in row:
                            if 'Instagram' in button.text:
                                await message.click(data=button.data)
                                break
            
            time.sleep(2)
            
            # Vérifier si le compte est dans la liste
            async for message in client.iter_messages(self.smm_bot_username, limit=1):
                if instagram_username in message.text:
                    logging.info(f"Compte Instagram {instagram_username} trouvé dans la liste")
                    return True
            
            logging.warning(f"Compte Instagram {instagram_username} non trouvé dans la liste")
            return False
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du compte Instagram: {e}")
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

def main_menu():
    """Menu principal du bot"""
    bot = SMMBot()
    
    while True:
        print(f"\n{Fore.CYAN}=== Menu Principal ==={Style.RESET_ALL}")
        print("1. Démarrer le bot")
        print("2. Ajouter un compte Telegram")
        print("3. Ajouter un compte Instagram")
        print("4. Voir les comptes enregistrés")
        print("5. Quitter")
        
        choice = input("\nVotre choix: ")
        
        if choice == "1":
            import asyncio
            asyncio.run(bot.start_bot())
        elif choice == "2":
            phone = input("Numéro de téléphone (format international): ")
            bot.add_telegram_account(phone)
        elif choice == "3":
            username = input("Nom d'utilisateur Instagram: ")
            password = input("Mot de passe Instagram: ")
            bot.add_instagram_account(username, password)
        elif choice == "4":
            print("\nComptes Telegram:", list(bot.telegram_accounts.keys()))
            print("Comptes Instagram:", list(bot.instagram_accounts.keys()))
        elif choice == "5":
            break
        else:
            print("Choix invalide")

if __name__ == "__main__":
    main_menu() 