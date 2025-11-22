from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

TOKEN = '8166576314:AAEZvY5L0hBwbVJThe6bw2BNVARie285vHI'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi!我是老吴的机器人RW🤖")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        welcome_msg = f"""欢迎 {member.full_name} 加入 LaoWu 社区。
我是老吴，有事说事，没事聊认知。
发泄情绪请找 @Laowu_ServiceBot，干扰他人者踢。

Twitter: https://x.com/121980719Wu

祝我们一起好运 ！"""
        await update.message.reply_text(welcome_msg)

async def keyword_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "hello" in text:
        await update.message.reply_text("Hey there 👋 How can I help you today?")
    elif "service" in text:
        await update.message.reply_text("耐心等待🚀")

def main():
    # 创建 Application 实例
    application = Application.builder().token(TOKEN).build()
    
    # 添加处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_reply))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    
    # 启动机器人
    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

