import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()  # .envファイルから読み込み（ローカルテスト用）

TOKEN = os.getenv("DISCORD_TOKEN")  # Railwayに環境変数として設定する

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()  # スラッシュコマンドの同期
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="uwaa", description="うわー！")
async def send(ctx):
        await ctx.send('こんにちは！私はBotです。')

bot.run(TOKEN)

