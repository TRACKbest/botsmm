import os
import json
import time
import random
import logging
from datetime import datetime
from telethon import TelegramClient, events
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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
        self.driver = None
        
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

    def get_api_credentials(self, phone):
        """Obtient automatiquement les identifiants API Telegram"""
        try:
            # Initialiser le driver Chrome
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            self.driver = uc.Chrome(options=options)
            
            # Accéder à la page de connexion
            self.driver.get('https://my.telegram.org/auth')
            time.sleep(2)
            
            # Entrer le numéro de téléphone
            phone_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "phone_number"))
            )
            phone_input.send_keys(phone)
            
            # Cliquer sur le bouton de connexion
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            time.sleep(2)
            
            # Attendre le code de confirmation
            code = input(f'Entrez le code reçu sur Telegram pour {phone}: ')
            
            # Entrer le code
            code_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "phone_code"))
            )
            code_input.send_keys(code)
            
            # Cliquer sur le bouton de confirmation
            confirm_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            confirm_button.click()
            time.sleep(2)
            
            # Aller à la page des outils API
            self.driver.get('https://my.telegram.org/apps')
            time.sleep(2)
            
            # Remplir le formulaire de création d'application
            app_title = "SMM Bot"
            short_name = "smmbot"
            platform = "Desktop"
            description = "SMM Bot for automation"
            
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "app_title"))
            )
            title_input.send_keys(app_title)
            
            short_name_input = self.driver.find_element(By.NAME, "app_shortname")
            short_name_input.send_keys(short_name)
            
            platform_select = self.driver.find_element(By.NAME, "app_platform")
            platform_select.send_keys(platform)
            
            description_input = self.driver.find_element(By.NAME, "app_description")
            description_input.send_keys(description)
            
            # Soumettre le formulaire
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            time.sleep(2)
            
            # Récupérer les identifiants API
            api_id = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='form-control input-field']"))
            ).text
            
            api_hash = self.driver.find_element(By.XPATH, "//span[@class='form-control input-field']").text
            
            # Sauvegarder les identifiants dans le fichier .env
            with open('.env', 'a') as f:
                f.write(f'\nAPI_ID={api_id}\nAPI_HASH={api_hash}')
            
            return api_id, api_hash
            
        except Exception as e:
            logging.error(f"Erreur lors de l'obtention des identifiants API: {e}")
            return None, None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def add_telegram_account(self, phone):
        """Ajoute un compte Telegram"""
        try:
            # Vérifier si les identifiants API existent
            if not os.getenv('API_ID') or not os.getenv('API_HASH'):
                print("Obtention des identifiants API...")
                api_id, api_hash = self.get_api_credentials(phone)
                if not api_id or not api_hash:
                    logging.error("Impossible d'obtenir les identifiants API")
                    return False
                # Recharger les variables d'environnement
                load_dotenv()
            
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

    def init_instagram_driver(self):
        """Initialise le driver Chrome pour Instagram"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless')  # Mode sans interface graphique
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            self.driver = uc.Chrome(options=options)
            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation du driver: {e}")
            return False

    def login_instagram(self, username, password):
        """Connecte le compte Instagram via Selenium"""
        try:
            self.driver.get('https://www.instagram.com/accounts/login/')
            time.sleep(3)  # Attente du chargement de la page

            # Remplir le formulaire de connexion
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_input = self.driver.find_element(By.NAME, "password")

            username_input.send_keys(username)
            password_input.send_keys(password)

            # Cliquer sur le bouton de connexion
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()

            # Attendre que la connexion soit terminée
            time.sleep(5)
            
            # Vérifier si la connexion a réussi
            if "login" not in self.driver.current_url:
                return True
            return False
        except Exception as e:
            logging.error(f"Erreur lors de la connexion Instagram: {e}")
            return False

    def execute_instagram_task(self, task):
        """Exécute une tâche Instagram"""
        if not self.current_instagram_account:
            logging.error("Aucun compte Instagram actif")
            return False

        try:
            account = self.instagram_accounts[self.current_instagram_account]
            
            if not self.driver:
                if not self.init_instagram_driver():
                    return False
                
            if not self.login_instagram(account['username'], account['password']):
                return False

            if 'like' in task['action'].lower():
                self.driver.get(task['link'])
                time.sleep(3)
                like_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@class='_aamj']//button"))
                )
                like_button.click()
                logging.info(f"Like effectué sur {task['link']}")
            
            elif 'comment' in task['action'].lower():
                self.driver.get(task['link'])
                time.sleep(3)
                comment_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//textarea[@placeholder='Add a comment…']"))
                )
                comment_input.send_keys(task['comment'])
                post_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                post_button.click()
                logging.info(f"Commentaire posté sur {task['link']}")
            
            elif 'follow' in task['action'].lower():
                self.driver.get(task['link'])
                time.sleep(3)
                follow_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Follow')]"))
                )
                follow_button.click()
                logging.info(f"Follow effectué sur {task['link']}")

            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'exécution de la tâche: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

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