import os
import json
import time
import random
import logging
from datetime import datetime
from telethon import TelegramClient, events
from instagrapi import Client as InstagramClient
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Initialisation
init()
load_dotenv()

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
        
        # Création des dossiers nécessaires
        os.makedirs('accounts/telegram', exist_ok=True)
        os.makedirs('accounts/instagram', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Chargement des comptes existants
        self.load_accounts()

    def load_accounts(self):
        """Charge les comptes depuis les fichiers de configuration"""
        try:
            if os.path.exists('accounts/telegram/accounts.json'):
                with open('accounts/telegram/accounts.json', 'r') as f:
                    self.telegram_accounts = json.load(f)
            
            if os.path.exists('accounts/instagram/accounts.json'):
                with open('accounts/instagram/accounts.json', 'r') as f:
                    self.instagram_accounts = json.load(f)
        except Exception as e:
            logging.error(f"Erreur lors du chargement des comptes: {e}")

    def save_accounts(self):
        """Sauvegarde les comptes dans les fichiers de configuration"""
        try:
            with open('accounts/telegram/accounts.json', 'w') as f:
                json.dump(self.telegram_accounts, f)
            
            with open('accounts/instagram/accounts.json', 'w') as f:
                json.dump(self.instagram_accounts, f)
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des comptes: {e}")

    def add_telegram_account(self, phone):
        """Ajoute un compte Telegram"""
        try:
            client = TelegramClient(f'accounts/telegram/{phone}', 
                                  os.getenv('API_ID'), 
                                  os.getenv('API_HASH'))
            client.connect()
            
            if not client.is_user_authorized():
                client.send_code_request(phone)
                code = input(f'Entrez le code reçu pour {phone}: ')
                client.sign_in(phone, code)
            
            self.telegram_accounts[phone] = {
                'phone': phone,
                'session': f'accounts/telegram/{phone}.session'
            }
            self.save_accounts()
            logging.info(f"Compte Telegram {phone} ajouté avec succès")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du compte Telegram: {e}")
            return False

    def add_instagram_account(self, username, password):
        """Ajoute un compte Instagram"""
        try:
            client = InstagramClient()
            client.login(username, password)
            
            self.instagram_accounts[username] = {
                'username': username,
                'password': password
            }
            self.save_accounts()
            logging.info(f"Compte Instagram {username} ajouté avec succès")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du compte Instagram: {e}")
            return False

    def parse_task_message(self, message):
        """Parse le message de tâche du bot SMM"""
        task = {
            'link': None,
            'action': None,
            'comment': None,
            'reward': None
        }
        
        try:
            lines = message.split('\n')
            for line in lines:
                if 'Link :' in line:
                    task['link'] = line.split('Link :')[1].strip()
                elif 'Action :' in line:
                    task['action'] = line.split('Action :')[1].strip()
                elif 'Comment:' in line:
                    task['comment'] = line.split('Comment:')[1].strip()
                elif 'Reward :' in line:
                    task['reward'] = line.split('Reward :')[1].strip()
            
            return task
        except Exception as e:
            logging.error(f"Erreur lors du parsing du message: {e}")
            return None

    def execute_instagram_task(self, task):
        """Exécute une tâche Instagram"""
        if not self.current_instagram_account:
            logging.error("Aucun compte Instagram actif")
            return False

        try:
            client = InstagramClient()
            account = self.instagram_accounts[self.current_instagram_account]
            client.login(account['username'], account['password'])

            if 'like' in task['action'].lower():
                media_id = client.media_id_from_url(task['link'])
                client.media_like(media_id)
                logging.info(f"Like effectué sur {task['link']}")
            
            elif 'comment' in task['action'].lower():
                media_id = client.media_id_from_url(task['link'])
                client.media_comment(media_id, task['comment'])
                logging.info(f"Commentaire posté sur {task['link']}")
            
            elif 'follow' in task['action'].lower():
                user_id = client.user_id_from_username(task['link'].split('/')[-2])
                client.user_follow(user_id)
                logging.info(f"Follow effectué sur {task['link']}")

            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'exécution de la tâche: {e}")
            return False

    def start_bot(self):
        """Démarre le bot"""
        if not self.telegram_accounts or not self.instagram_accounts:
            logging.error("Aucun compte configuré")
            return

        try:
            # Connexion au premier compte Telegram
            first_phone = list(self.telegram_accounts.keys())[0]
            client = TelegramClient(
                self.telegram_accounts[first_phone]['session'],
                os.getenv('API_ID'),
                os.getenv('API_HASH')
            )
            
            @client.on(events.NewMessage(from_users=self.smm_bot_username))
            async def handle_new_message(event):
                message = event.message.text
                task = self.parse_task_message(message)
                
                if task:
                    if self.execute_instagram_task(task):
                        # Attente aléatoire entre les actions
                        time.sleep(random.randint(30, 60))
                    else:
                        logging.error("Échec de l'exécution de la tâche")

            client.start()
            client.run_until_disconnected()
            
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
            bot.start_bot()
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