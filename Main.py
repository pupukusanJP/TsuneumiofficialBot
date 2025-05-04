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
    print(f'ログインしました: {bot.user}')
    try:
        # スラッシュコマンドを同期
        synced = await tree.sync()
        print(f"スラッシュコマンドを {len(synced)} 個同期しました")
    except Exception as e:
        print(f"コマンドの同期中にエラーが発生しました: {e}")

# スラッシュコマンドを定義
@tree.command(name="verify", description="認証を行いロールを付与します")
async def verify(interaction: discord.Interaction):
    guild = interaction.guild
    member = interaction.user
    role_name = "Verified"

    # ロールを検索
    role = discord.utils.get(guild.roles, name=role_name)

    # ユーザーがすでにロールを持っているか確認
    if role in member.roles:
        await interaction.response.send_message(f"⚠️ {member.mention}さんはすでに認証済みです。", ephemeral=True)
        return

    # ロールがない場合、自動作成
    if not role:
        try:
            role = await guild.create_role(
                name=role_name,
                colour=discord.Colour.green(),  # 緑色
                permissions=discord.Permissions(send_messages=True)  # 必要な権限を設定
            )
            await interaction.response.send_message(f"✅ ロール '{role_name}' を作成しました！", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ BOTにロールを作成する権限がありません。管理者に確認してください。", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"⚠️ ロールの作成中にエラーが発生しました: {e}", ephemeral=True)
            return

    # ロールをユーザーに付与
    try:
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ {member.mention} さんにロール '{role_name}' を付与しました！", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("⚠️ BOTにロールを付与する権限がありません。管理者に確認してください。", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ ロール付与中にエラーが発生しました: {e}", ephemeral=True)
bot.run(TOKEN)

