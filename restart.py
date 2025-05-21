import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "7305046364:AAGHE_yJ84H63C_eBHGw_YKK1JVLmE8XTgo"
AUTHORIZED_USERS = [7673456476]  # e.g., [123456789]

async def restart_ubuntu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ Unauthorized!")
        return

    try:
        # Execute reboot command directly (no SSH needed)
        os.system("sudo reboot")
        await update.message.reply_text("🔄 Ubuntu is restarting...")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("restart", restart_ubuntu))
    print("Bot is running. Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()