import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import requests
from flask import Flask
from threading import Thread
import os

# --- 1. سيرفر ويب للبقاء متصلاً على Render ---
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

# --- 3. نافذة الأزرار التفاعلية (اللاعبين + الصور + الروابط) ---
class ServerView(View):
    def __init__(self, players_data, ip, banner_url, icon_url):
        super().__init__(timeout=None)
        self.players_data = players_data
        self.ip = ip
        self.banner_url = banner_url
        self.icon_url = icon_url

    # زر إظهار اللاعبين
    @discord.ui.button(label="👥 اللاعبين", style=discord.ButtonStyle.gray)
    async def show_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.players_data:
            return await interaction.response.send_message("❌ لا يوجد لاعبين متصلين.", ephemeral=True)
        header = "🆔 | الاسم | Steam ID\n" + "—"*30 + "\n"
        lines = [f"[{p.get('id')}] {p.get('name')[:15]} | {next((id for id in p.get('identifiers', []) if 'steam' in id), 'N/A').replace('steam:', '')}" for p in self.players_data[:25]]
        await interaction.response.send_message(f"```txt\n{header +  '\\n'.join(lines)}```", ephemeral=True)

    # زر روابط الـ JSON (السكربتات)
    @discord.ui.button(label="📜 ملفات السيرفر", style=discord.ButtonStyle.gray)
    async def show_json(self, interaction: discord.Interaction, button: discord.ui.Button):
        content = (
            f"🔗 **روابط البيانات المباشرة:**\n"
            f"🔹 `players.json`: [اضغط هنا](http://{self.ip}/players.json)\n"
            f"🔹 `info.json`: [اضغط هنا](http://{self.ip}/info.json)\n"
            f"🔹 `dynamic.json`: [اضغط هنا](http://{self.ip}/dynamic.json)"
        )
        await interaction.response.send_message(content, ephemeral=True)

    # زر عرض الصور (لوقو وبانر)
    @discord.ui.button(label="🖼️ صور السيرفر", style=discord.ButtonStyle.gray)
    async def show_images(self, interaction: discord.Interaction, button: discord.ui.Button):
        content = f"🖼️ **روابط الصور الأصلية:**\n"
        if self.icon_url: content += f"🔹 [اضغط هنا لمشاهدة اللوقو]({self.icon_url})\n"
        if self.banner_url: content += f"🔹 [اضغط هنا لمشاهدة البانر]({self.banner_url})"
        await interaction.response.send_message(content, ephemeral=True)

# --- 4. أمر السلاش /فحص ---
@bot.tree.command(name="فحص", description="فحص شامل (لاعبين، صور، ملفات JSON)")
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
            banner_url = vars.get('banner_detail')
            icon_url = f"https://servers-live.fivem.net/servers/icon/{server_code}.png"
            
            embed = discord.Embed(title=f"🌐 {data.get('hostname', 'Server')[:50]}", color=0x2b2d31)
            
            # عرض البانر واللوقو في الرسالة الأساسية
            if banner_url: embed.set_image(url=banner_url)
            embed.set_thumbnail(url=icon_url)

            # معلومات السيرفر الأساسية
            embed.add_field(name="💀 Server IP", value=f"`{ip}`", inline=False)
            embed.add_field(name="👥 المتصلين", value=f"`{data['clients']} / {data['sv_maxclients']}`", inline=True)
            embed.add_field(name="💎 الدعم", value=f"`{vars.get('sv_premium', 'Basic').upper()}`", inline=True)
            
            embed.set_footer(text="King Bot • استخدم الأزرار أدناه للمزيد من التفاصيل")
            
            view = ServerView(data.get('players', []), ip, banner_url, icon_url)
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send("❌ تعذر العثور على السيرفر.")
    except:
        await interaction.followup.send("⚠️ حدث خطأ في الاتصال.")

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get('BOT_TOKEN'))
