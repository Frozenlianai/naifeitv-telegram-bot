from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from naifeitv_spider.spider import NaifeiTVSpider
import os
from bot.db import BotDB
import time
from telegram.constants import ChatType
from telegram.ext import ChatMemberHandler

# 直接在此处填写你的机器人Token，例如：
# BOT_TOKEN = '123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'  # 这里填你的机器人Token

spider = NaifeiTVSpider()
db = BotDB()

async def st(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('欢迎使用奈飞TV搜索机器人！\n使用 /so 关键词 搜索影片。')

async def se(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('请提供搜索关键词，例如 /se 误杀')
        return
    keyword = ' '.join(context.args)
    user = update.effective_user
    db.log_user_search(user.id, user.username, keyword)
    results = spider.search_movies(keyword)
    if not results:
        await update.message.reply_text('未找到相关影片。')
        return
    for movie in results:
        caption = (
            f"🎬 *{movie['title']}*\n"
            f"⭐ 评分: {movie.get('score', '无')}\n"
            f"📝 简介: {movie.get('desc', '无')}\n"
            f"🏷️ 类型: {movie.get('type', '无')}\n"
        )
        buttons = [
            [InlineKeyboardButton('🔎 详情', callback_data=f"detail|{movie['id']}")]
        ]
        await update.message.reply_photo(
            photo=movie.get('thumb', ''),
            caption=caption,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(buttons)
        )

async def gr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    groups = db.get_groups()
    if not groups:
        await update.message.reply_text('暂无群组统计信息。')
        return
    reply = ''
    for gid, name, count, link in groups:
        reply += f"群组: {name}\n人数: {count}\n邀请链接: {link or '无'}\n---\n"
    await update.message.reply_text(reply)

async def us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    days = 10
    if context.args and context.args[0].isdigit():
        days = int(context.args[0])
    stats = db.get_user_stats(days)
    if not stats:
        await update.message.reply_text(f'{days}天内暂无用户搜索记录。')
        return
    reply = f'{days}天内用户搜索统计：\n'
    for uid, uname, count, queries in stats:
        reply += f"用户: {uname or uid}\n搜索次数: {count}\n片名: {queries}\n---\n"
    await update.message.reply_text(reply)

async def so(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('请提供搜索关键词，例如 /so 误杀')
        return
    keyword = ' '.join(context.args)
    user = update.effective_user
    db.log_user_search(user.id, user.username, keyword)
    results = spider.search_movies(keyword)
    if not results:
        await update.message.reply_text('未找到相关影片。')
        return
    reply = ''
    for movie in results[:5]:
        reply += f"🎬 *{movie['title']}*\n📝 {movie.get('desc', '无')}\n---\n"
    await update.message.reply_text(reply, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith('detail|'):
        movie_id = data.split('|')[1]
        detail = spider.get_movie_detail(movie_id)
        # 片源切换按钮
        source_buttons = [
            [InlineKeyboardButton(f"{src['name']}", callback_data=f"play|{movie_id}|{src['id']}") for src in detail['sources']]
        ] if detail['sources'] else []
        # 集数展示
        episodes = detail.get('episodes', [])
        ep_text = ''
        if episodes:
            ep_text = '\n'.join([f"第{idx+1}集: {ep['title']}" for idx, ep in enumerate(episodes)])
        caption = (
            f"🎬 *{detail['title']}*\n"
            f"📝 简介: {detail.get('desc', '无')}\n"
            f"📺 集数: {len(episodes)}\n"
            f"{ep_text}\n"
        )
        await query.edit_message_caption(
            caption=caption,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(source_buttons) if source_buttons else None
        )
    elif data.startswith('play|'):
        _, movie_id, source_id = data.split('|')
        play_url = spider.get_play_url(movie_id, source_id)
        await query.edit_message_caption(
            caption=f"▶️ [点击这里播放]({play_url})",
            parse_mode='Markdown',
            reply_markup=None
        )

async def group_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.chat_member.chat
    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        # 获取群组成员数和邀请链接（需管理员权限）
        member_count = await context.bot.get_chat_member_count(chat.id)
        try:
            invite_link = (await context.bot.create_chat_invite_link(chat.id)).invite_link
        except Exception:
            invite_link = None
        db.upsert_group(chat.id, chat.title, member_count, invite_link)

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('st', st))
    app.add_handler(CommandHandler('se', se))
    app.add_handler(CommandHandler('so', so))
    app.add_handler(CommandHandler('gr', gr))
    app.add_handler(CommandHandler('us', us))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(ChatMemberHandler(group_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.run_polling() 