import os
import random
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv
import platform

# .envファイルからトークンを読み込む
load_dotenv()
TOKEN = os.getenv("TOKEN")

# 特定のギルドIDを指定
GUILD_ID = 1258077953326190713  # ギルドIDを設定

# ボットのインテントを設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージコンテンツインテントを有効にする
intents.emojis = True
intents.guilds = True

# ボットの初期化
bot = commands.Bot(command_prefix="/", intents=intents)

# FlaskでUptimeRobotのPingを受け付ける
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"

# Webサーバーを別スレッドで実行
def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

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

# Webサーバーとボットを並行して実行
keep_alive()
bot.run(TOKEN)



