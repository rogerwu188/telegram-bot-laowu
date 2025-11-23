from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import os

# 配置
TELEGRAM_TOKEN = '8166576314:AAEZvY5L0hBwbVJThe6bw2BNVARie285vHI'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# 初始化 OpenAI 客户端
openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")
else:
    print("⚠️  OPENAI_API_KEY not set")

# 存储用户对话历史
conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    
    await update.message.reply_text("""
👋 你好！我是老吴的智能助手 RW

我接入了 ChatGPT，可以回答各种问题！

💬 直接发送消息给我，我会智能回复
🔄 发送 /reset 重置对话
❓ 发送 /help 查看帮助

让我们开始聊天吧！
""")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    await update.message.reply_text("""
📖 帮助菜单

可用命令：
/start - 开始使用并重置对话
/reset - 重置对话历史
/help - 显示此帮助

💡 使用技巧：
• 直接发送问题，我会用 ChatGPT 回答
• 我会记住对话上下文
• 使用 /reset 开始新话题

🎯 我可以帮你：
• 回答问题
• 写作协助
• 代码帮助
• 翻译文本
• 创意建议
• 等等...
""")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """重置对话历史"""
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("✅ 对话已重置，让我们开始新的话题吧！")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """欢迎新成员"""
    for member in update.message.new_chat_members:
        welcome_msg = f"""欢迎 {member.full_name} 加入 LaoWu 社区。
我是老吴，有事说事，没事聊认知。
发泄情绪请找 @Laowu_ServiceBot，干扰他人者踢。

Twitter: https://x.com/121980719Wu

祝我们一起好运 ！"""
        await update.message.reply_text(welcome_msg)

async def chat_with_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """使用 ChatGPT 回复消息"""
    # 检查 OpenAI 客户端
    if not openai_client:
        await update.message.reply_text(
            "❌ ChatGPT 功能未配置\n\n请在 Railway Variables 中设置 OPENAI_API_KEY"
        )
        return
    
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # 初始化用户对话历史
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # 添加用户消息
    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })
    
    # 限制历史长度
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]
    
    try:
        # 显示正在输入
        await update.message.chat.send_action("typing")
        
        # 调用 ChatGPT
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你是老吴的智能助手，名叫 RW。你聪明、友好、幽默，擅长回答各种问题。回答要简洁明了，适合在 Telegram 聊天中阅读。"
                },
                *conversation_history[user_id]
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # 获取回复
        assistant_message = response.choices[0].message.content
        
        # 添加到历史
        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # 发送回复
        await update.message.reply_text(assistant_message)
        
    except Exception as e:
        error_msg = f"❌ 处理消息时出错：{str(e)}\n\n"
        error_msg += "请检查：\n"
        error_msg += "1. OPENAI_API_KEY 是否正确\n"
        error_msg += "2. OpenAI 账户是否有余额\n"
        error_msg += "3. 网络连接是否正常"
        
        await update.message.reply_text(error_msg)
        print(f"❌ Error in chat_with_gpt: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("🤖 Telegram Bot with ChatGPT")
    print("=" * 50)
    print(f"OpenAI API Key: {'✅ Configured' if OPENAI_API_KEY else '❌ Not set'}")
    print(f"OpenAI Client: {'✅ Ready' if openai_client else '❌ Not initialized'}")
    print("=" * 50)
    
    # 创建 Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # 添加处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_gpt))
    
    # 启动
    print("✅ Bot is running...")
    print("=" * 50)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
