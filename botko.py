from telethon.sync import TelegramClient
from telethon import functions, types
import asyncio
import random
import time
import logging

# Configuration du logging pour le débogage
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paramètres de connexion
api_id = 22200892
api_hash = '0892dc9bc7a249ca4124ecd1e2795525'
phone = '+261344897133'
bot_username = 'smmkingdomtasksbot'

# Initialisation du client
client = TelegramClient('smmkingdom_session', api_id, api_hash)

async def human_like_delay(min_sec=1, max_sec=4):
    """Délai aléatoire pour imiter le comportement humain"""
    delay = random.uniform(min_sec, max_sec)
    logger.info(f"⏳ Délai humain: {delay:.2f}s")
    await asyncio.sleep(delay)

async def find_and_click_button(messages, button_text, limit=5):
    """Trouve et clique sur un bouton dans les messages"""
    async for message in client.iter_messages(bot_username, limit=limit):
        if message.buttons:
            for row in message.buttons:
                for button in row:
                    if button_text.lower() in button.text.lower():
                        logger.info(f"✅ Bouton '{button.text}' trouvé")
                        await human_like_delay(0.5, 2)
                        await message.click(text=button.text)
                        return True
    return False

async def main():
    try:
        # Connexion avec délai aléatoire avant de commencer
        await human_like_delay(2, 5)
        await client.start(phone)
        logger.info("✅ Connecté au client Telegram")

        # Recherche et clic sur le bouton Tasks
        if not await find_and_click_button(bot_username, "Tasks"):
            logger.error("❌ Bouton 'Tasks' non trouvé")
            return

        # Délai supplémentaire après avoir cliqué sur Tasks
        await human_like_delay(2, 4)

        # Recherche et clic sur le bouton Instagram
        if not await find_and_click_button(bot_username, "Instagram", limit=3):
            logger.error("❌ Bouton 'Instagram' non trouvé")
            return

        # Délai après avoir sélectionné Instagram
        await human_like_delay(1, 3)

        # Attendre et traiter la réponse du bot
        async for message in client.iter_messages(bot_username, limit=2):
            if message.text and "username" in message.text.lower():
                logger.info("📋 Le bot demande le nom d'utilisateur")
                # Ici vous pourriez ajouter la logique pour répondre avec un username
                break

        # Marquer les messages comme lus
        await client.send_read_acknowledge(bot_username)

    except Exception as e:
        logger.error(f"❌ Erreur: {str(e)}", exc_info=True)
    finally:
        await human_like_delay(1, 3)  # Délai avant déconnexion
        await client.disconnect()
        logger.info("🔴 Déconnecté")

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())