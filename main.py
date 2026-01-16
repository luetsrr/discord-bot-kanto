import discord
from discord import app_commands
from discord import ui
import os
import re
import asyncio
import requests
import json
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- Webサーバー設定 (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 設定の読み込み ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# 【重要】HTML対応版のGASをデプロイして、新しいURLをここに貼ってください
GAS_URL = "https://script.google.com/macros/s/AKfycbwtYIsn8ZB5nMJvjXtZDQx6LXvEYEyLG0kH1N2rXI-FUtlBz2n5LR2jlFcFLbcgbiv49Q/exec"
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# --- Botの初期設定 ---
intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ==========================================
#  【共通】GASへの送信リクエスト関数
# ==========================================
def post_to_gas(to_email, subject, body):
    payload = {
        "to": to_email,
        "subject": subject,
        "body": body
    }
    response = requests.post(GAS_URL, json=payload)
    if response.status_code != 200:
        raise Exception(f"GASエラー: {response.text}")

# ==========================================
#  ロジック: 受付メール送信 (send_entry)
# ==========================================
def send_entry_logic(to_email, name, year, month):
    subject = f"【うぃーすた関東】ご参加を承りました【{year}年{month}月例会】"
    
    # 【修正】HTMLメール化したので、単純な改行(\n)だけで確実に隙間ができます。
    # \n\n\n とすることで、<br><br><br> に変換され、絶対に削除されない空白行になります。
    body = f"""

{name}　様


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
    post_to_gas(to_email, subject, body)
    return body

# ==========================================
#  ロジック: LINE招待送信 (send_line_invite)
# ==========================================
def send_invite_logic(emails_str, year, month, url):
    recipient_list = [addr.strip() for addr in emails_str.split(',')]
    sent_emails = [] 
    
    subject = f"【うぃーすた関東】LINEオープンチャットへご参加お願いします【{year}年{month}月例会】"
    
    # 【修正】こちらも単純な改行でOKです
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
    
    for email in recipient_list:
        if email:
            post_to_gas(email, subject, body)
            sent_emails.append(email)
            
    return sent_emails

# ==========================================
#  UI定義: ボタンを押した後の入力フォーム (Modal)
# ==========================================
class EntryModal(ui.Modal, title='受付完了メール送信の確認'):
    def __init__(self, default_email, default_name, default_year, default_month):
        super().__init__()
        self.email_input = ui.TextInput(label="メールアドレス", default=default_email)
        self.name_input = ui.TextInput(label="ニックネーム", default=default_name)
        
        self.year_input = ui.TextInput(
            label="開催年", 
            default=default_year, 
            min_length=2, 
            max_length=2
        )
        self.month_input = ui.TextInput(
            label="開催月", 
            default=default_month, 
            min_length=1, 
            max_length=2
        )

        self.add_item(self.email_input)
        self.add_item(self.name_input)
        self.add_item(self.year_input)
        self.add_item(self.month_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            email = self.email_input.value
            name = self.name_input.value
            year = int(self.year_input.value)
            month = int(self.month_input.value)

            await asyncio.to_thread(send_entry_logic, email, name, year, month)

            await interaction.followup.send(
                f"受付完了メールを送信しました！\n"
                f"送信先メールアドレス: `{email}`\n"
                f"ニックネーム: {name}\n"
                f"対象: {year}年{month}月例会"
            )
            print(f"GAS経由で送信成功: {email}")
            
            # 元のメッセージを削除
            try:
                await interaction.message.delete()
            except Exception:
                pass

        except Exception as e:
            await interaction.followup.send(f"送信に失敗しました。\nエラー内容: {e}")

# ==========================================
#  UI定義: メッセージの下に出るボタン (View)
# ==========================================
class EntryButtonView(ui.View):
    def __init__(self, email, name, year, month):
        super().__init__(timeout=None)
        self.email = email
        self.name = name
        self.year = year
        self.month = month

    @discord.ui.button(label="受付完了メールを送信", style=discord.ButtonStyle.primary, emoji="📝")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EntryModal(self.email, self.name, self.year, self.month)
        await interaction.response.send_modal(modal)

# ==========================================
#  イベント: メッセージ受信時の自動検知処理
# ==========================================
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if "**新しい参加お申し込みがありました！**" in message.content:
        try:
            content = message.content
            
            email_match = re.search(r"メールアドレス:\s*(.+)", content)
            name_match = re.search(r"ニックネーム:\s*(.+)", content)
            date_match = re.search(r"参加希望日:\s*(\d{4})[/-](\d{1,2})", content)

            email = email_match.group(1).strip() if email_match else ""
            name = name_match.group(1).strip() if name_match else ""
            
            if date_match:
                year = date_match.group(1)[-2:]
                month = date_match.group(2)
            else:
                year = "26"
                month = ""

            view = EntryButtonView(email, name, year, month)
            await message.channel.send(
                "参加お申し込みを検知しました。定員などに問題がなければ、下のボタンを押して受付完了メールを送信してください。", 
                view=view
            )

        except Exception as e:
            print(f"自動検知エラー: {e}")

# ==========================================
#  Bot起動時の処理
# ==========================================
@client.event
async def on_ready():
    GUILD_ID = discord.Object(id=1448201700811866277)
    tree.copy_global_to(guild=GUILD_ID)
    await tree.sync(guild=GUILD_ID)
    
    print(f'ログインしました: {client.user}')
    print(f'サーバー(ID: {GUILD_ID.id}) に同期しました。')
    print('※ephemeral=False 設定済み')

# ==========================================
#  コマンド1: 受付メール (send_entry)
# ==========================================
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
        await asyncio.to_thread(send_entry_logic, email_address, user_name, year, month)
        
        await interaction.followup.send(
            f"受付完了メールを送信しました！\n"
            f"送信先メールアドレス: `{email_address}`\n"
            f"ニックネーム: {user_name}\n"
            f"対象: {year}年{month}月例会"
        )
    except Exception as e:
        await interaction.followup.send(f"送信に失敗しました。\nエラー内容: {e}")

# ==========================================
#  コマンド2: LINE招待一斉送信 (send_line_invite)
# ==========================================
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
        sent_list = await asyncio.to_thread(send_invite_logic, emails, year, month, url)
        count = len(sent_list)
        
        sent_list_str = "\n".join(sent_list)

        msg = (
            f"オプチャの招待リンクを一斉送信しました！\n"
            f"送信数: {count} 件\n"
            f"対象: {year}年{month}月\n"
            f"リンク: {url}\n"
            f"送信先メールアドレス:\n"
            f"```\n{sent_list_str}\n```"
        )
        
        if len(msg) > 1900:
            msg = (
                f"オプチャの招待リンクを一斉送信しました！\n"
                f"送信数: {count} 件\n"
                f"対象: {year}年{month}月\n"
                f"リンク: {url}\n"
                f"送信先メールアドレス:\n"
                f"(人数が多すぎるため表示を省略しました)"
            )

        await interaction.followup.send(msg)
        print(f"GAS経由で一斉送信成功: {count}件")

    except Exception as e:
        await interaction.followup.send(f"送信に失敗しました。\nエラー内容: {e}")
        print(f"エラー発生: {e}")

# --- Botの起動 ---
keep_alive()
client.run(TOKEN)
