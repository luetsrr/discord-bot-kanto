import discord
from discord import app_commands
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 設定の読み込み ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

# --- Botの初期設定 ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    """Bot起動時に実行される処理"""
    # あなたのサーバーID
    GUILD_ID = discord.Object(id=1448201700811866277)

    tree.copy_global_to(guild=GUILD_ID)
    await tree.sync(guild=GUILD_ID)
    
    print(f'ログインしました: {client.user}')
    print(f'サーバー(ID: {GUILD_ID.id}) に同期しました。')
    print('※このBotの返信は「あなただけに表示されています」となります。')

# --- コマンド1: 受付メール (個別) ---
@tree.command(name="send_entry", description="例会参加の受付完了メールを送信します")
@app_commands.rename(
    email_address="メールアドレス",
    user_name="ニックネーム",
    year="開催年",
    month="開催月"
)
async def send_entry_command(
    interaction: discord.Interaction, 
    email_address: str, 
    user_name: str, 
    year: int,
    month: int
):
    await interaction.response.defer(ephemeral=False)

    try:
        subject = f"【うぃーすた関東】ご参加を承りました【{year}年{month}月例会】"
        body = f"""
{user_name}　様


お世話になっております。

この度はうぃーすた関東の活動へご参加いただき、誠にありがとうございます。


{year}年{month}月例会へのご参加を承りました。

例会の詳細につきましてはLINEのオープンチャットにてご案内いたします。

例会当日の2週間前を目安に例会用オープンチャットへの招待リンクをご入力のメールアドレス宛にお送りいたしますのでお待ちください。


何かご不明な点やご心配なことなどがありましたらご遠慮なくお問い合わせください。

よろしくお願いいたします。


＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊
うぃーすた関東
メールアドレス：westu.kanto2@gmail.com
ホームページ：https://we-are-stutt.jimdofree.com/activities/westu-kanto
X（旧 Twitter）：https://x.com/westu_kanto2
Instagram：https://www.instagram.com/westu_kanto/
＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊
"""
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = email_address

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)

        await interaction.followup.send(
            f"受付メールを送信しました！\n"
            f"メールアドレス: `{email_address}`\n"
            f"ニックネーム: {user_name}\n"
            f"対象: {year}年{month}月例会"
        )
        print(f"送信成功: {email_address} / {year}年{month}月")

    except Exception as e:
        await interaction.followup.send(f"送信に失敗しました。\nエラー内容: {e}")
        print(f"エラー発生: {e}")


# --- コマンド2: LINE招待メール (一斉送信) ---
@tree.command(name="send_line_invite", description="LINEオープンチャットの招待リンクを一斉送信します")
@app_commands.rename(
    emails="メールアドレス",
    year="開催年",
    month="開催月",
    url="オプチャの招待リンク"
)
async def send_line_invite_command(
    interaction: discord.Interaction, 
    emails: str, 
    year: int, 
    month: int, 
    url: str
):
    await interaction.response.defer(ephemeral=False)

    try:
        # メールアドレスリストの整形
        recipient_list = [addr.strip() for addr in emails.split(',')]
        bcc_string = ", ".join(recipient_list)
        count = len(recipient_list)

        subject = f"【うぃーすた関東】LINEオープンチャットへご参加お願いします【{year}年{month}月例会】"

        body = f"""
{year}年{month}月例会に参加される皆さまへ


お世話になっております。

この度は、うぃーすた関東{year}年{month}月例会にご参加いただき、誠にありがとうございます。


例会用LINEオープンチャットを作成しましたので、下記リンクよりお忘れなくご参加お願いします。

{url}

例会に関する今後のご連絡はこちらでさせていただきます。

※オープンチャット内でのお名前はお好きなもので構いません。


何かご不明な点やご心配なことなどがありましたらご遠慮なくお問い合わせください。

よろしくお願いいたします。


＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊
うぃーすた関東
メールアドレス：westu.kanto2@gmail.com
ホームページ：https://we-are-stutt.jimdofree.com/activities/westu-kanto
X（旧 Twitter）：https://x.com/westu_kanto2
Instagram：https://www.instagram.com/westu_kanto/
＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊
"""

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = GMAIL_USER # Toは自分
        msg['Bcc'] = bcc_string # Bccに全員

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)

        await interaction.followup.send(
            f"オプチャの招待リンクを一斉送信しました！\n"
            f"送信数: {count} 件\n"
            f"対象: {year}年{month}月\n"
            f"リンク: {url}"
        )
        print(f"BCC送信成功: {count}件")

    except Exception as e:
        await interaction.followup.send(f"送信に失敗しました。\nエラー内容: {e}")
        print(f"エラー発生: {e}")

# --- Botの起動 ---
client.run(TOKEN)
