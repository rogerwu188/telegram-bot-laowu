from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import os
from openai import OpenAI

# 配置
TELEGRAM_TOKEN = '8166576314:AAEZvY5L0hBwbVJThe6bw2BNVARie285vHI'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '你的OpenAI_API_Key')

# 初始化 OpenAI 客户端
client = OpenAI(api_key=OPENAI_API_KEY)

# 存储用户对话历史（简单实现，生产环境建议使用数据库）
conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    user_id = update.effective_user.id
    conversation_history[user_id] = []  # 重置对话历史
    
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
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # 初始化用户对话历史
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # 添加用户消息到历史
    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })
    
    # 限制历史记录长度（避免 token 过多）
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]
    
    try:
        # 发送"正在输入"状态
        await update.message.chat.send_action("typing")
        
        # 调用 ChatGPT API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 使用 GPT-4o-mini 模型，性价比高
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
        
        # 获取 ChatGPT 的回复
        assistant_message = response.choices[0].message.content
        
        # 添加助手回复到历史
        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # 发送回复
        await update.message.reply_text(assistant_message)
        
    except Exception as e:
        error_message = f"❌ 抱歉，处理您的消息时出错了：{str(e)}\n\n请稍后重试或联系管理员。"
        await update.message.reply_text(error_message)
        print(f"Error: {e}")

def main():
    """主函数"""
    # 创建 Application 实例
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # 添加欢迎新成员处理器
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, 
        welcome
    ))
    
    # 添加 ChatGPT 消息处理器（处理所有文本消息，排除命令）
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        chat_with_gpt
    ))
    
    # 启动机器人
    print("🤖 Bot is starting with ChatGPT integration...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
