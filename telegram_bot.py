from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram import Update, ChatMember
from telegram.ext import ContextTypes
import os
import json
import requests
import re

# 配置
TELEGRAM_TOKEN = '8166576314:AAEZvY5L0hBwbVJThe6bw2BNVARie285vHI'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# 存储用户对话历史
conversation_history = {}

# 提币/要钱关键词
MONEY_KEYWORDS = ['提币', '要钱', '退钱', '还钱', '欠钱', '钱', '退款', '赔钱']

# 脏话关键词列表
BAD_WORDS = [
    '傻逼', '傻b', 'sb', '煞笔', '沙比',
    '垃圾', '废物', '智障', '白痴', '蠢货',
    '滚', '草泥马', 'cnm', '妈的', '操',
    '去死', '死全家', '狗东西', '畜生',
    '傻X', '傻x', '傻叉', '脑残', '弱智'
]

def contains_money_keywords(text):
    """检测文本中是否包含提币/要钱关键词"""
    text_lower = text.lower()
    for word in MONEY_KEYWORDS:
        if word in text_lower:
            return True
    return False

def contains_bad_words(text):
    """检测文本中是否包含脏话"""
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            return True
    return False

async def is_admin(update: Update, user_id: int) -> bool:
    """检查用户是否是管理员"""
    try:
        chat = update.effective_chat
        if chat.type == 'private':
            return False
        
        member = await chat.get_member(user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except:
        return False

def call_chatgpt(messages):
    """使用 HTTP requests 直接调用 OpenAI API"""
    if not OPENAI_API_KEY:
        return None, "API Key 未配置"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            OPENAI_API_URL,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'], None
        else:
            error_msg = f"API 错误 {response.status_code}: {response.text[:200]}"
            return None, error_msg
            
    except requests.exceptions.Timeout:
        return None, "请求超时，请重试"
    except requests.exceptions.RequestException as e:
        return None, f"网络错误: {str(e)[:100]}"
    except Exception as e:
        return None, f"未知错误: {str(e)[:100]}"

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

⚠️ 温馨提示：文明交流，友善沟通

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

⚠️ 特别提示：
• 请文明交流，友善沟通
• 关于提币/资金问题，请耐心等待
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
    user_message = update.message.text
    user_id = update.effective_user.id
    is_group = update.effective_chat.type in ['group', 'supergroup']
    
    # 优先级1：检测提币/要钱关键词（群组和私聊都生效）
    if contains_money_keywords(user_message):
        print(f"💰 检测到提币/要钱关键词！用户: {update.effective_user.first_name}, 消息: {user_message}")
        await update.message.reply_text("我正在努力赚钱，等公司业务好转了，就会处理。")
        return
    
    # 优先级2：如果在群组中，检查是否包含脏话
    if is_group:
        # 检查是否是管理员
        is_user_admin = await is_admin(update, user_id)
        
        # 如果不是管理员且包含脏话，触发反击
        if not is_user_admin and contains_bad_words(user_message):
            print(f"🎯 检测到脏话，触发反击！用户: {update.effective_user.first_name}, 消息: {user_message}")
            # 使用安全的反击回复
            safe_roasts = [
                "你才是",
                "你礼貌吗？",
                "建议你先学会好好说话",
                "注意素质",
                "文明点"
            ]
            import random
            roast_message = random.choice(safe_roasts)
            await update.message.reply_text(roast_message)
            return
    
    # 优先级3：正常 ChatGPT 对话
    # 检查 API Key
    if not OPENAI_API_KEY:
        await update.message.reply_text(
            "❌ ChatGPT 功能未配置\n\n"
            "请在 Railway Variables 中设置 OPENAI_API_KEY"
        )
        return
    
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
        
        # 准备消息
        messages = [
            {
                "role": "system",
                "content": "你是老吴的智能助手，名叫 RW。你聪明、友好、幽默，擅长回答各种问题。回答要简洁明了，适合在 Telegram 聊天中阅读。"
            },
            *conversation_history[user_id]
        ]
        
        # 调用 ChatGPT
        assistant_message, error = call_chatgpt(messages)
        
        if error:
            # 发生错误
            error_msg = f"❌ 调用 ChatGPT 时出错\n\n{error}\n\n"
            error_msg += "请检查：\n"
            error_msg += "1. OPENAI_API_KEY 是否正确\n"
            error_msg += "2. OpenAI 账户是否有余额\n"
            error_msg += "3. 网络连接是否正常"
            await update.message.reply_text(error_msg)
            # 移除最后添加的用户消息
            conversation_history[user_id].pop()
            return
        
        # 添加到历史
        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # 发送回复
        await update.message.reply_text(assistant_message)
        
    except Exception as e:
        error_msg = f"❌ 处理消息时出错\n\n{str(e)[:200]}"
        await update.message.reply_text(error_msg)
        print(f"❌ Error in chat_with_gpt: {e}")
        # 移除最后添加的用户消息
        if conversation_history[user_id]:
            conversation_history[user_id].pop()

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 Telegram Bot with ChatGPT & Auto Reply")
    print("=" * 60)
    print(f"OpenAI API Key: {'✅ Configured' if OPENAI_API_KEY else '❌ Not set'}")
    print(f"API URL: {OPENAI_API_URL}")
    print(f"💰 提币/要钱自动回复: ✅ 已启用")
    print(f"🎯 反击模式: ✅ 已启用（安全模式）")
    print(f"📝 监控提币关键词: {len(MONEY_KEYWORDS)} 个")
    print(f"📝 监控脏话关键词: {len(BAD_WORDS)} 个")
    
    # 测试 API 连接
    if OPENAI_API_KEY:
        print("🔍 Testing OpenAI API connection...")
        test_messages = [{"role": "user", "content": "test"}]
        response, error = call_chatgpt(test_messages)
        if error:
            print(f"❌ API test failed: {error}")
        else:
            print("✅ API test successful")
    
    print("=" * 60)
    
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
    print("=" * 60)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
