import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import requests
from flask import Flask
from threading import Thread
import os

# --- 1. سيرفر الويب للبقاء متصلاً على Render ---
app = Flask('')
@app.route('/')
def home(): return "King Bot is Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. إعدادات البوت ودعم أوامر السلاش ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # مزامنة أوامر السلاش مع ديسكورد
        await self.tree.sync()
        print(f"✅ تم مزامنة أوامر السلاش")

bot = MyBot()

# --- 3. نظام الأزرار لعرض اللاعبين ---
class PlayersView(View):
    def __init__(self, players_data):
        super().__init__(timeout=None)
        self.players_data = players_data

    @discord.ui.button(label="إظهار أسماء اللاعبين والأيديات", style=discord.ButtonStyle.green, emoji="👥")
    async def show_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.players_data:
            return await interaction.response.send_message("لا يوجد لاعبين متصلين حالياً.", ephemeral=True)
        
        players_text = "🆔 | الاسم | Steam ID\n" + "-"*30 + "\n"
        for p in self.players_data[:25]:
            steam = next((id for id in p.get('identifiers', []) if 'steam' in id), 'لا يوجد')
            players_text += f"[{p.get('id')}] | {p.get('name')} | {steam}\n"
        
        await interaction.response.send_message(f"```txt\n{players_text}```", ephemeral=True)

# --- 4. أمر السلاش /فحص ---
@bot.tree.command(name="فحص", description="فحص سيرفر FiveM أو RedM وجلب كافة التفاصيل")
@app_commands.describe(link="ضع رابط السيرفر أو كود الـ CFX هنا")
async def check(interaction: discord.Interaction, link: str):
    await interaction.response.defer() # لإعطاء البوت وقت لجلب البيانات
    
    server_code = link.split('/')[-1]
    url = f"https://servers-frontend.fivem.net/api/servers/single/{server_code}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()['Data']
            ip = data['connectEndPoints'][0]
            vars = data.get('vars', {})
            
            embed = discord.Embed(title=f"🚀 {data.get('hostname', 'سيرفر')[:50]}", color=0x2b2d31)

            # الصور
            banner = vars.get('banner_detail')
            if banner: embed.set_image(url=banner)
            embed.set_thumbnail(url=f"https://servers-live.fivem.net/servers/icon/{server_code}.png")

            # البيانات
            embed.add_field(name="💀 Server IP", value=f"`{ip}`", inline=False)
            embed.add_field(name="👥 اللاعبين", value=f"🟢 {data['clients']} / 🔴 {data['sv_maxclients']}", inline=True)
            embed.add_field(name="🌍 الدولة", value=f"{vars.get('locale', 'Unknown')}", inline=True)
            
            # الرست ومعلومات إضافية
            rest_info = "غير محدد"
            for tag in data.get('tags', []):
                if 'restart' in tag.lower(): rest_info = tag
            
            embed.add_field(name="🔄 جدولة الرست", value=f"`{rest_info}`", inline=False)
            embed.set_footer(text="تم الفحص بواسطة King Bot")
            
            view = PlayersView(data.get('players', []))
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send("❌ فشل العثور على السيرفر.")
    except:
        await interaction.followup.send("⚠️ حدث خطأ أثناء جلب البيانات.")

# --- 5. التشغيل ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get('BOT_TOKEN'))
