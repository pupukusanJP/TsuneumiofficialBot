import os
import random
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv
import platform
import aiohttp
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
from discord.ext import commands
from discord.ui import View, Button

# 既にあればOK、なければ以下を追加
last_spam_report_time = {}

# もしuser_message_timesもまだならこちらも宣言
user_message_times = defaultdict(list)


# .envファイルからトークンを読み込む
load_dotenv()
TOKEN = os.getenv("TOKEN")

# 特定のギルドIDを指定
GUILD_ID = 1258077953326190713  # ギルドIDを設定

# ボットのインテントを設定
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

# ボットの初期化
bot = commands.Bot(command_prefix="/", intents=intents)

# FlaskでUptimeRobotのPingを受け付ける
app = Flask(__name__)

# ユーザーIDごとのメッセージ送信時刻リストを保持
user_message_times = defaultdict(list)

# スパム検知チャンネルID（適宜変更してください）
SPAM_REPORT_CHANNEL_ID = 1376216186257145876
locked_channels = set()
jst = pytz.timezone('Asia/Tokyo')


@app.route("/")
def home():
    return "Bot is running!"

# Webサーバーを別スレッドで実行
def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

class UnlockButtonView(View):
    def __init__(self, channel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label="🔓 スパム解除", style=discord.ButtonStyle.green)
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ この操作を行う権限がありません。", ephemeral=True)
            return

        current_overwrite = self.channel.overwrites_for(self.channel.guild.default_role)
        if current_overwrite.send_messages is not False:
            await interaction.response.send_message("ℹ️ このチャンネルはすでに解除されています。", ephemeral=True)
            self.stop()
            return

        await self.channel.edit(sync_permissions=True)
        await interaction.response.send_message("✅ カテゴリーと同期してロック解除しました。", ephemeral=True)
        locked_channels.discard(self.channel.id)
        self.stop()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(jst)
    user_id = message.author.id
    channel_id = message.channel.id

    # ロック中チャンネルでは非管理者のメッセージを削除
    if channel_id in locked_channels:
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            return

    user_message_times[user_id].append(now)

    # 5秒以内の履歴のみ保持
    threshold = now - timedelta(seconds=5)
    user_message_times[user_id] = [t for t in user_message_times[user_id] if t > threshold]

    if len(user_message_times[user_id]) >= 3:
        last_report = last_spam_report_time.get(user_id)
        if last_report and (now - last_report) < timedelta(seconds=60):
            return

        report_channel = bot.get_channel(SPAM_REPORT_CHANNEL_ID)
        if report_channel:
            embed = discord.Embed(
                title="⚠️ スパム検知 ⚠️",
                color=discord.Color.red(),
                timestamp=now
            )
            embed.add_field(name="ユーザー", value=f"{message.author} (ID: {user_id})", inline=False)
            embed.add_field(name="メッセージ", value=message.content or "（内容なし）", inline=False)
            embed.add_field(name="チャンネル", value=message.channel.mention, inline=False)
            embed.set_footer(text="検知日時（JST）")

            # チャンネルロック処理
            overwrite = message.channel.overwrites_for(message.guild.default_role)
            overwrite.send_messages = False
            await message.channel.set_permissions(message.guild.default_role, overwrite=overwrite)
            locked_channels.add(channel_id)

            view = UnlockButtonView(message.channel)
            await report_channel.send(embed=embed, view=view)

        last_spam_report_time[user_id] = now
        user_message_times[user_id].clear()

    await bot.process_commands(message)


# ボットが準備できたときに呼ばれるイベント
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="常海電鉄"))

    try:
        # コマンドをグローバルで同期
        await bot.tree.sync()
        print("🔁 Synced commands globally.")
    except Exception as e:
        print(f"❌ Global sync error: {e}")

    # ギルド同期を確認
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        try:
            # ギルド単位でコマンド同期
            await bot.tree.sync(guild=guild)
            print(f"🔁 Synced commands for guild {guild.name}")
        except Exception as e:
            print(f"❌ Sync error for guild {guild.name}: {e}")

# おみくじコマンド
@bot.tree.command(name="omikuzi", description="おみくじを引きます")
async def omikuzi(interaction: discord.Interaction):
    fortunes = ["大吉", "中吉", "小吉", "末吉", "凶", "大凶"]
    result = random.choice(fortunes)
    await interaction.response.send_message(f"🎴 あなたの運勢は… **{result}**！")

# ラッキーカラーコマンド
@bot.tree.command(name="luckycolor", description="今日のラッキーカラーを教えます")
async def luckycolor(interaction: discord.Interaction):
    colors = ["赤", "青", "黄色", "緑", "紫", "ピンク", "白", "黒"]
    color = random.choice(colors)
    await interaction.response.send_message(f"🎨 今日のラッキーカラーは **{color}** です！")

# 常海電鉄のロゴを送信するコマンド
@bot.tree.command(name="tsuneumi", description="常海電鉄のロゴを送信します")
async def tsuneumi(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ロゴの画像",
        description="常海のロゴだよ！",
        color=discord.Color.blue()
    )
    embed.set_image(url="https://img.atwiki.jp/rbxjptrain/attach/403/2403/%E5%90%8D%E7%A7%B0%E6%9C%AA%E8%A8%AD%E5%AE%9A%E3%81%AE%E3%83%87%E3%82%B6%E3%82%A4%E3%83%B3%20%284%29.png")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="routemap", description="常海電鉄の路線図を送信します")
async def routemap(interaction: discord.Interaction):
    embed = discord.Embed(
        title="路線図",
        description="常海電鉄の路線図だよ",
        color=discord.Color.blue()
    )
    embed.set_image(url="https://img.atwiki.jp/rbxjptrain/attach/403/2427/%E8%B7%AF%E7%B7%9A%E5%9B%B3.png")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="hi", description="挨拶してくれるよ")
async def hi(interaction: discord.Interaction):
    await interaction.response.send_message(f"hi")

@bot.tree.command(name="botinfo", description="Botの情報を送信します")
async def botinfo(interaction: discord.Interaction):
    # Bot情報の埋め込みメッセージ
    embed = discord.Embed(
        title="Botの情報",
        description="以下はBotの詳細情報です。",
        color=discord.Color.blue()
    )
    embed.add_field(name="Bot名", value=bot.user.name, inline=True)
    embed.add_field(name="BotのID", value=bot.user.id, inline=True)
    embed.add_field(name="サーバー数", value=len(bot.guilds), inline=True)
    embed.add_field(name="ユーザー数", value=len([member for guild in bot.guilds for member in guild.members]), inline=True)
    embed.add_field(name="BotのPing", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="使用している言語", value="Python", inline=True)
    embed.add_field(name="Pythonのバージョン", value=platform.python_version(), inline=True)
    embed.set_footer(text=f"Botの作成者: pupuku_777")
    
    # メッセージ送信
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="allemoji", description="指定されたサーバーのすべての絵文字を送信します")
async def allemoji(interaction: discord.Interaction):
    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        return await interaction.response.send_message("指定されたギルドが見つかりません。Botがそのサーバーに参加しているか確認してください。", ephemeral=True)

    if not guild.emojis:
        return await interaction.response.send_message("このサーバーにはカスタム絵文字がありません。", ephemeral=True)

    emoji_list = [str(emoji) for emoji in guild.emojis]
    embed = discord.Embed(title=f"{guild.name} の絵文字一覧", color=discord.Color.blurple())

    chunk_size = 50
    chunks = [emoji_list[i:i + chunk_size] for i in range(0, len(emoji_list), chunk_size)]

    for i, chunk in enumerate(chunks[:25]):  # Embedフィールドは最大25
        embed.add_field(name=f"絵文字セット {i+1}", value=" ".join(chunk), inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="groupinfo", description="Robloxグループの情報を取得します")
async def groupinfo(interaction: discord.Interaction):
    group_id = 34072257  # group_id をここで直接設定

    await interaction.response.defer()
    async with aiohttp.ClientSession() as session:
        # グループ基本情報
        group_url = f"https://groups.roblox.com/v1/groups/{group_id}"
        async with session.get(group_url) as resp:
            if resp.status != 200:
                await interaction.followup.send("グループ情報を取得できませんでした。")
                return
            group_data = await resp.json()

        # ロール（人数）情報
        roles_url = f"https://groups.roblox.com/v1/groups/{group_id}/roles"
        async with session.get(roles_url) as resp:
            if resp.status != 200:
                await interaction.followup.send("メンバー情報を取得できませんでした。")
                return
            roles_data = await resp.json()
            total_members = sum(role["memberCount"] for role in roles_data["roles"])

        # オーナー
        owner = group_data.get("owner")
        owner_name = owner["username"] if owner else "オーナーなし"

        embed = discord.Embed(
            title=f"{group_data['name']} のグループ情報",
            description=group_data.get('description') or "説明なし",
            color=discord.Color.green()
        )
        embed.add_field(name="設立日", value=group_data.get("created", "不明"), inline=False)
        embed.add_field(name="メンバー数", value=str(total_members), inline=True)
        embed.add_field(name="オーナー", value=owner_name, inline=True)
        embed.add_field(name="グループID", value=str(group_id), inline=True)
        embed.set_thumbnail(url=group_data.get("emblemUrl", ""))

        await interaction.followup.send(embed=embed)

# Webサーバーとボットを並行して実行
keep_alive()
bot.run(TOKEN)



