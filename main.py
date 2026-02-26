import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import requests
from flask import Flask
from threading import Thread
import os

# --- 1. سيرفر ويب للبقاء متصلاً ---
app = Flask('')
@app.route('/')
def home(): return "King Bot is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. إعدادات البوت ودعم السلاش ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ تم مزامنة أوامر السلاش")

bot = MyBot()

# --- 3. نافذة اللاعبين التفاعلية ---
class PlayersView(View):
    def __init__(self, players_data):
        super().__init__(timeout=None)
        self.players_data = players_data

    @discord.ui.button(label="👤 إظهار قائمة اللاعبين والأيديات", style=discord.ButtonStyle.green, emoji="🔍")
    async def show_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.players_data:
            return await interaction.response.send_message("❌ لا يوجد لاعبين متصلين حالياً.", ephemeral=True)
        
        header = "🆔 | الاسم | Steam ID\n" + "—"*35 + "\n"
        lines = [f"[{p.get('id')}] {p.get('name')[:15]} | {next((id for id in p.get('identifiers', []) if 'steam' in id), 'N/A').replace('steam:', '')}" for p in self.players_data[:30]]
        
        output = header + "\n".join(lines)
        if len(self.players_data) > 30: output += f"\n... و {len(self.players_data) - 30} آخرين."
        await interaction.response.send_message(f"```txt\n{output}```", ephemeral=True)

# --- 4. أمر السلاش /فحص ---
@bot.tree.command(name="فحص", description="فحص شامل للسيرفر مع صورة البانر الأصلية")
@app_commands.describe(link="رابط السيرفر أو كود الـ CFX")
async def check(interaction: discord.Interaction, link: str):
    await interaction.response.defer()
    
    server_code = link.split('/')[-1]
    url = f"https://servers-frontend.fivem.net/api/servers/single/{server_code}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()['Data']
            vars = data.get('vars', {})
            ip = data['connectEndPoints'][0]
            
            embed = discord.Embed(title=f"🏰 {data.get('hostname', 'Server')[:50]}", color=0x2b2d31)

            # --- هنا التعديل: جلب صورة البانر الأصلية التي وضعها صاحب السيرفر ---
            banner_url = vars.get('banner_detail') # هذا هو الرابط الرسمي للبانر
            if banner_url:
                embed.set_image(url=banner_url) # وضع الصورة في أسفل الرسالة
            
            # وضع الأيقونة الصغيرة في الزاوية
            embed.set_thumbnail(url=f"https://servers-live.fivem.net/servers/icon/{server_code}.png")

            # الحقول المعلوماتية
            embed.add_field(name="💀 Server IP", value=f"`{ip}`", inline=False)
            embed.add_field(name="👥 اللاعبين", value=f"🟢 `{data['clients']}` / 🔴 `{data['sv_maxclients']}`", inline=True)
            embed.add_field(name="🔑 صاحب السيرفر", value=f"[{data.get('ownerName', 'Unknown')}](https://forum.cfx.re/u/{data.get('ownerName')})", inline=True)
            
            # معلومات الرست
            rest_info = next((tag for tag in data.get('tags', []) if 'restart' in tag.lower()), "غير محدد")
            embed.add_field(name="🔄 جدولة الرست", value=f"`{rest_info}`", inline=False)

            embed.set_footer(text="King Bot • تم سحب صورة السيرفر الأصلية")
            
            view = PlayersView(data.get('players', []))
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send("❌ السيرفر غير موجود.")
    except:
        await interaction.followup.send("⚠️ خطأ في جلب البيانات.")

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get('BOT_TOKEN'))
