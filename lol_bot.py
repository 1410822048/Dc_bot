import os
import discord
from discord.ext import commands, tasks
from datetime import time
import asyncio

# 獲取 Discord Token
TOKEN = os.environ.get('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("請設置環境變數 DISCORD_TOKEN！")

# 啟用特權意圖
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 固定邀請的用戶 ID
FIXED_USERS = [
    542600173986250762, 627844121939279892, 394103882055417866,
    547051019473780767, 417292881028579338
]

# 在全局變數
current_invite_message_id = None
processing_active = False  # 新增處理狀態標記

# 存儲同意參加的用戶
accepted_users = set()

# 緩存頻道對象
target_channel = None
voice_channel = None

# 指定的語音頻道 ID
VOICE_CHANNEL_ID = 681835115994939395  # 替換為你的語音頻道 ID

# 固定的邀請訊息內容
INVITE_MESSAGE = (
    "**單中開幹**\n"
    "今晚要一起玩《咆嘯深淵》嗎？\n"
    "邀請成員：\n" +
    "\n".join([f"<@{user_id}>" for user_id in FIXED_USERS]) +
    "\n\n如果想参加，請點擊 1️⃣；如果不想参加，請點擊 0️⃣\n"
    "\n"
    "**15 分鐘後結算**。"
)
# 定时任务区
INVITE_TIME = time(13, 30)
SHUTDOWN_TIME = time(14, 5)
CHECK_TIME = time(14, 0)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

    # 獲取目標頻道和語音頻道對象
    global target_channel, voice_channel
    for guild in bot.guilds:
        # 獲取第一個文字頻道
        if not target_channel:
            target_channel = guild.text_channels[0] if guild.text_channels else None
        # 獲取指定的語音頻道
        if not voice_channel:
            voice_channel = guild.get_channel(VOICE_CHANNEL_ID)

    if target_channel:
        print(f"Bot 已找到目標頻道: {target_channel.name}")
    else:
        print("Bot 未找到目標頻道。")

    if voice_channel:
        print(f"Bot 已找到語音頻道: {voice_channel.name}")
    else:
        print("Bot 未找到語音頻道。")

    # 啟動定時任務
    tasks_to_start = [daily_invite, stop_bot_task, morning_check]
    for task in tasks_to_start:
        if not task.is_running():
            task.start()

# 13:30 發送邀請訊息
@tasks.loop(time=INVITE_TIME)
async def daily_invite():
    global current_invite_message_id, processing_active
    if target_channel:
        try:
            accepted_users.clear()
            processing_active = True  # 開啟處理模式
            message = await target_channel.send(INVITE_MESSAGE)
            current_invite_message_id = message.id  # 記錄當前訊息ID
            await asyncio.gather(
                message.add_reaction("1️⃣"),
                message.add_reaction("0️⃣")
            )
            
            # 等待 15 分鐘
            await asyncio.sleep(15 * 60)  # 15 分鐘 = 900 秒

            processing_active = False
            current_invite_message_id = None

            # 檢查同意參加的用戶數量
            if len(accepted_users) < 3:
                await target_channel.send("**今天PASS🫠**")

                # 將語音頻道中的所有用戶移出
                if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
                    for member in voice_channel.members:
                        try:
                            await member.move_to(None)  # 將用戶移出語音頻道
                            await target_channel.send(f"{member.mention} 已從語音頻道中移出。")
                        except discord.Forbidden:
                            await target_channel.send(f"**沒有權限移動 {member.mention}。**")
                            continue
                        except discord.HTTPException as e:
                            await target_channel.send(f"**移動用戶時出錯: {e}**")
                            continue
                else:
                    await target_channel.send("**找不到指定的語音頻道，請檢查 頻道_ID 是否正確。**")
            else:
                    # 建立嵌入物件並設定直接 GIF 連結
                    embed = discord.Embed()
                    embed.set_image(url="https://media1.tenor.com/m/LIhHu8kdj8oAAAAd/%E4%B8%81%E7%89%B9-%E7%88%B8%E7%88%B8%E7%99%BC%E9%A3%86%E4%BA%86.gif")
    
                    # 同時發送文字和 GIF
                    await target_channel.send(embed=embed)

        except Exception as e:
            print(f"發送邀請訊息出錯: {e}")
            processing_active = False
            current_invite_message_id = None

        daily_invite.stop()

    else:
        print("沒有找到目標頻道，請檢查 Bot 是否已加入伺服器。")


@tasks.loop(time=CHECK_TIME)
async def morning_check():
    """晚上 10 点检查成员是否在语音频道"""
    if not target_channel or not voice_channel:
        return

    if len(accepted_users) < 3:
        return    

    try:
        # 获取需要检查的用户对象
        missing_users = []
        for user_id in accepted_users.copy():  # 使用副本遍历避免修改原始集合
            member = voice_channel.guild.get_member(user_id)
            if not member:
                continue  # 用户不在服务器中
                
            # 检查是否在语音频道
            if not member.voice or member.voice.channel != voice_channel:
                missing_users.append(member.mention)

        # 发送提醒
        if missing_users:
            mention_list = " ".join(missing_users)
            await target_channel.send(
                f"{mention_list}\n"
                "**全世界都在等妳！**\n"
                "請立即加入語音！"
            )
            
    except Exception as e:
        print(f"失敗: {e}")


# 14:05 關閉機器人
@tasks.loop(time=SHUTDOWN_TIME)
async def stop_bot_task():
    print("機器人已關閉！")
    await bot.close()  # 登出機器人

# 監聽表情反應
@bot.event
async def on_raw_reaction_add(payload):
    """處理用戶的表情反應"""
    if any([
        payload.user_id == bot.user.id,
        not processing_active,  # 新增狀態檢查
        payload.message_id != current_invite_message_id,  # 檢查是否為當前訊息
        payload.channel_id != target_channel.id,
        payload.user_id not in FIXED_USERS
    ]):
        return

    try:
        user = await bot.fetch_user(payload.user_id)
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if payload.emoji.name == "1️⃣":
            await _handle_reaction(message, user, accept=True)
        elif payload.emoji.name == "0️⃣":
            await _handle_reaction(message, user, accept=False)
    except Exception as e:
        print(f"處理表情反應時出錯: {e}")


async def _handle_reaction(message, user, accept=True):
    """處理表情反應的內部邏輯"""
    if not processing_active or message.id != current_invite_message_id:
        return  # 雙重驗證確保時效
    try:
        # 移除其他反應
        other_emoji = "0️⃣" if accept else "1️⃣"
        for reaction in message.reactions:
            if reaction.emoji == other_emoji:
                async for reaction_user in reaction.users():
                    if reaction_user.id == user.id:
                        await message.remove_reaction(other_emoji, user)

        # 更新參加者列表
        if accept:
            accepted_users.add(user.id)
            await message.channel.send(f"**{user.mention} 已同意參加！**")

            # 生成語音頻道邀請連結
            if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
                try:
                    invite = await voice_channel.create_invite(max_uses=1, unique=True)
                    await message.channel.send(f"{user.mention} 請點擊 🎧 __**[這裡](<{invite.url}>)**__ 加入！")
                except discord.Forbidden:
                    await message.channel.send("**沒有權限生成邀請連結。**")
                except discord.HTTPException as e:
                    await message.channel.send(f"**生成邀請連結時出錯: {e}**")
            else:
                await message.channel.send("**找不到語音頻道，請檢查 頻道_ID 是否正確。**")
        else:
            accepted_users.discard(user.id)
            await message.channel.send(f"**{user.mention} 已取消參加！**")

            # 將用戶從語音頻道移出
            member = message.guild.get_member(user.id)
            if member.voice and member.voice.channel == voice_channel:
                await member.move_to(None)
                await message.channel.send(f"**{user.mention} 已從語音中移出。**")
    except discord.Forbidden:
        await message.channel.send(f"**無法移動 {user.mention}，權限不足。**")
    except discord.HTTPException as e:
        await message.channel.send(f"**移動用戶時出錯: {e}**")
        
# 啟動機器人
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"機器人啟動失敗: {e}")