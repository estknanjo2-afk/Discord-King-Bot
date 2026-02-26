import discord
from discord.ext import commands
import requests
from flask import Flask
from threading import Thread
import os

# سيرفر ويب بسيط لإبقاء البوت حياً
app = Flask('')
@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# إعدادات البوت
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ تم تشغيل البوت بنجاح باسم: {bot.user}')

@bot.command()
async def فحص(ctx, link: str):
    code = link.split('/')[-1]
    url = f"https://servers-frontend.fivem.net/api/servers/single/{code}"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            data = r.json()['Data']
            embed = discord.Embed(title=f"📊 سيرفر: {data.get('hostname', 'Unknown')[:30]}", color=0x00ff00)
            embed.add_field(name="🌐 IP:", value=f"`{data['connectEndPoints'][0]}`", inline=False)
            embed.add_field(name="👥 لاعبين:", value=f"{data['clients']}/{data['sv_maxclients']}", inline=True)
            embed.set_footer(text="تم الفحص بواسطة بوتك العربي")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ السيرفر غير موجود أو الكود خطأ.")
    except:
        await ctx.send("⚠️ حدث خطأ أثناء جلب البيانات.")

keep_alive()
# جلب التوكن من إعدادات الموقع (Environment Variables)
token = os.environ.get('BOT_TOKEN')
bot.run(token)
