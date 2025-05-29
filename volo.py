import os
import json
import random
import time
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import Message
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_DIR = os.path.join(BASE_DIR, "accounts")
TELEGRAM_DIR = os.path.join(ACCOUNTS_DIR, "telegram")
INSTAGRAM_DIR = os.path.join(ACCOUNTS_DIR, "instagram")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")

# Create directories if they don't exist
os.makedirs(TELEGRAM_DIR, exist_ok=True)
os.makedirs(INSTAGRAM_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Load or initialize accounts
def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    return {"telegram": [], "instagram": []}

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f, indent=4)

# Logging function
def log_action(account, action, status, message):
    log_file = os.path.join(LOGS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.txt")
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.now()}] Account: {account} | Action: {action} | Status: {status} | Message: {message}\n")

# Telegram account management
def add_telegram_account():
    phone = input("Enter Telegram phone number (e.g., +1234567890): ")
    api_id = input("Enter your Telegram API ID: ")
    api_hash = input("Enter your Telegram API Hash: ")

    client = TelegramClient(os.path.join(TELEGRAM_DIR, phone), api_id, api_hash)
    client.connect()

    if not client.is_user_authorized():
        client.send_code_request(phone)
        code = input("Enter the OTP code sent to your Telegram: ")
        try:
            client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("Enter your 2FA password: ")
            client.sign_in(password=password)

    client.disconnect()
    accounts = load_accounts()
    accounts["telegram"].append({"phone": phone, "api_id": api_id, "api_hash": api_hash})
    save_accounts(accounts)
    print(f"Telegram account {phone} added successfully!")

def remove_telegram_account():
    accounts = load_accounts()
    print("Telegram accounts:")
    for i, acc in enumerate(accounts["telegram"]):
        print(f"{i+1}. {acc['phone']}")
    choice = int(input("Select account to remove (number): ")) - 1
    if 0 <= choice < len(accounts["telegram"]):
        phone = accounts["telegram"][choice]["phone"]
        os.remove(os.path.join(TELEGRAM_DIR, f"{phone}.session"))
        accounts["telegram"].pop(choice)
        save_accounts(accounts)
        print(f"Telegram account {phone} removed!")
    else:
        print("Invalid choice.")

# Instagram account management
def add_instagram_account():
    username = input("Enter Instagram username: ")
    password = input("Enter Instagram password: ")

    cl = Client()
    session_file = os.path.join(INSTAGRAM_DIR, f"{username}.json")
    try:
        cl.login(username, password)
        cl.dump_settings(session_file)
        accounts = load_accounts()
        accounts["instagram"].append({"username": username, "password": password})
        save_accounts(accounts)
        print(f"Instagram account {username} added successfully!")
    except Exception as e:
        print(f"Failed to add Instagram account: {e}")

def remove_instagram_account():
    accounts = load_accounts()
    print("Instagram accounts:")
    for i, acc in enumerate(accounts["instagram"]):
        print(f"{i+1}. {acc['username']}")
    choice = int(input("Select account to remove (number): ")) - 1
    if 0 <= choice < len(accounts["instagram"]):
        username = accounts["instagram"][choice]["username"]
        os.remove(os.path.join(INSTAGRAM_DIR, f"{username}.json"))
        accounts["instagram"].pop(choice)
        save_accounts(accounts)
        print(f"Instagram account {username} removed!")
    else:
        print("Invalid choice.")

# Parse SMM bot messages
def parse_task(message):
    task = {"link": None, "action": None, "comment": None, "reward": None}
    lines = message.split("\n")
    for line in lines:
        if "Link :" in line:
            task["link"] = line.split("Link :")[1].strip()
        elif "Action :" in line:
            action = line.split("Action :")[1].strip().lower()
            if "like" in action:
                task["action"] = "like"
            elif "follow" in action:
                task["action"] = "follow"
            elif "comment" in action:
                task["action"] = "comment"
                next_line = lines[lines.index(line) + 1]
                if "Comment:" in next_line:
                    task["comment"] = next_line.split("Comment:")[1].strip()
        elif "Reward :" in line:
            task["reward"] = line.split("Reward :")[1].strip()
    return task

# Execute Instagram tasks and mark as completed
def execute_instagram_task(cl, task, username, client, message):
    try:
        if task["action"] == "like":
            media_id = cl.media_id(cl.media_pk_from_url(task["link"]))
            cl.media_like(media_id)
            log_action(username, f"like (Reward: {task['reward']})", "✅ Success", f"Liked post {task['link']}")
        elif task["action"] == "follow":
            user_id = cl.user_id_from_username(task["link"].split("/")[-2])
            cl.user_follow(user_id)
            log_action(username, f"follow (Reward: {task['reward']})", "✅ Success", f"Followed {task['link']}")
        elif task["action"] == "comment":
            media_id = cl.media_id(cl.media_pk_from_url(task["link"]))
            cl.media_comment(media_id, task["comment"])
            log_action(username, f"comment (Reward: {task['reward']})", "✅ Success", f"Commented on {task['link']}")

        # Mark task as completed on Telegram bot
        if isinstance(message, Message) and message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if button.text == "Completed":
                        client(telethon.tl.functions.messages.GetBotCallbackAnswerRequest(
                            peer=message.peer_id,
                            msg_id=message.id,
                            data=button.data
                        ))
                        log_action(username, "task_completion", "✅ Success", "Marked task as completed on SMM bot")
                        break
    except (LoginRequired, ClientError) as e:
        log_action(username, f"{task['action']} (Reward: {task['reward']})", "❌ Failure", f"Account issue: {e}")
        return False
    except Exception as e:
        log_action(username, f"{task['action']} (Reward: {task['reward']})", "❌ Failure", f"Task failed: {e}")
    return True

# Main bot loop
def start_bot():
    accounts = load_accounts()
    if not accounts["telegram"] or not accounts["instagram"]:
        print("Please add at least one Telegram and Instagram account!")
        return

    # Connect to Telegram SMM bot
    tg_acc = accounts["telegram"][0]  # Use first Telegram account
    client = TelegramClient(
        os.path.join(TELEGRAM_DIR, tg_acc["phone"]),
        tg_acc["api_id"],
        tg_acc["api_hash"]
    )
    client.connect()
    if not client.is_user_authorized():
        print("Telegram session expired. Please re-add the account.")
        return

    # Get messages from SMM bot
    smm_bot = client.get_entity("@SMMKingdomBot")
    messages = client.get_messages(smm_bot, limit=10)

    tasks = []
    for msg in messages:
        task = parse_task(msg.text)
        if task["link"] and task["action"]:
            task["message"] = msg  # Store the message object for callback
            tasks.append(task)

    if not tasks:
        print("No tasks found from SMM bot.")
        client.disconnect()
        return

    # Loop through Instagram accounts and execute tasks
    for ig_acc in accounts["instagram"]:
        print(f"Processing Instagram account: {ig_acc['username']}")
        cl = Client()
        session_file = os.path.join(INSTAGRAM_DIR, f"{ig_acc['username']}.json")
        if os.path.exists(session_file):
            cl.load_settings(session_file)
            cl.login(ig_acc["username"], ig_acc["password"])
        else:
            cl.login(ig_acc["username"], ig_acc["password"])
            cl.dump_settings(session_file)

        for task in tasks:
            if not execute_instagram_task(cl, task, ig_acc["username"], client, task["message"]):
                print(f"Skipping account {ig_acc['username']} due to errors.")
                break
            time.sleep(random.uniform(5, 10))  # Anti-ban delay

        # Save session and move to next account
        cl.dump_settings(session_file)
        time.sleep(random.uniform(10, 20))  # Delay between accounts

    client.disconnect()
    print("All tasks completed!")

# Display accounts
def show_accounts():
    accounts = load_accounts()
    print("\nTelegram accounts:")
    for acc in accounts["telegram"]:
        print(f"- {acc['phone']}")
    print("\nInstagram accounts:")
    for acc in accounts["instagram"]:
        print(f"- {acc['username']}")

# Main menu
def main():
    while True:
        print("\n=== SMM Bot Menu ===")
        print("1. Start the bot (automatic tasks)")
        print("2. Add a Telegram account")
        print("3. Add an Instagram account")
        print("4. Remove a Telegram account")
        print("5. Remove an Instagram account")
        print("6. Show accounts")
        print("7. Update bot (not implemented)")
        print("8. Quit")
        choice = input("Select an option (1-8): ")

        try:
            if choice == "1":
                start_bot()
            elif choice == "2":
                add_telegram_account()
            elif choice == "3":
                add_instagram_account()
            elif choice == "4":
                remove_telegram_account()
            elif choice == "5":
                remove_instagram_account()
            elif choice == "6":
                show_accounts()
            elif choice == "7":
                print("Update functionality not implemented.")
            elif choice == "8":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Try again.")
        except Exception as e:
            print(f"An error occurred: {e}")
            log_action("System", "menu", "⚠️ Warning", f"Error in menu: {e}")
            time.sleep(2)  # Brief pause before restarting

if __name__ == "__main__":
    main()