from telethon.sync import TelegramClient
from telethon import functions, types
import asyncio
import random
import time

api_id = 22200892  # Ton vrai API ID
api_hash = '0892dc9bc7a249ca4124ecd1e2795525'  # Ton vrai API Hash
phone = '+261344897133'  # Ton numéro
bot_username = 'smmkingdomtasksbot'

# Initialisation du client avec une session persistante
client = TelegramClient('smmkingdom_session', api_id, api_hash)

async def main():
    try:
        # Connexion au client
        await client.start(phone)
        print("✅ Connecté au client Telegram")

        # Recherche du bouton "✏️Tasks✏️" dans les derniers messages
        async for message in client.iter_messages(bot_username, limit=5):  # Limite à 5 messages
            if message.buttons:
                for row in message.buttons:
                    for button in row:
                        if "Tasks" in button.text:
                            print("✅ Bouton 'Tasks' trouvé et cliqué")
                            await message.click(text=button.text)
                            break

        # Attente aléatoire pour imiter un comportement humain
        await asyncio.sleep(random.uniform(1.5, 3.0))  # Délai aléatoire entre 1.5 et 3 secondes
        await client.send_read_acknowledge(bot_username)  # Marquer les messages comme lus

        # Recherche du bouton "Instagram"
        async for message in client.iter_messages(bot_username, limit=3):  # Limite à 3 messages
            if message.buttons:
                for row in message.buttons:
                    for button in row:
                        if button.text == "Instagram":
                            print("✅ Bouton 'Instagram' trouvé et cliqué")
                            await message.click(text="Instagram")
                            return

        print("❌ Bouton 'Instagram' non trouvé")

    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
    finally:
        await client.disconnect()  # Déconnexion propre

# Exécution du code
with client:
    client.loop.run_until_complete(main())
