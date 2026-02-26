import discord
from discord.ext import commands
import requests
from flask import Flask
from threading import Thread
import os

# --- 1. سيرفر ويب وهمي لمنع إغلاق البوت على Render ---
app = Flask('')

@app.route('/')
def home():
    return "البوت متصل ويعمل بنجاح!"

def run():
    # تشغيل السيرفر على بورت 8080 وهو المفضل لـ Render
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. إعدادات بوت الديسكورد ---
intents = discord.Intents.default()
intents.message_content = True  # لقراءة الرسائل والأوامر
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ تم تسجيل الدخول بنجاح باسم: {bot.user}')

@bot.command()
async def فحص(ctx, link: str):
    """أمر لفحص سيرفرات FiveM عن طريق الرابط أو الكود"""
    # استخراج كود السيرفر من الرابط (مثل bokeep)
    server_code = link.split('/')[-1]
    
    url = f"https://servers-frontend.fivem.net/api/servers/single/{server_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()['Data']
            
            # تصميم الرسالة (Embed) لتشبه الصورة التي أرفقتها
            embed = discord.Embed(title=f"🌐 {data.get('hostname', 'سيرفر FiveM')[:50]}", color=0x2f3136)
            
            # الآي بي
            ip = data['connectEndPoints'][0]
            embed.add_field(name="💀 Server IP 💀", value=f"`{ip}`", inline=False)
            
            # الاستضافة والدولة
            embed.add_field(name="⚠️ ISP ⚠️", value=data.get('ownerName', 'غير معروف'), inline=True)
            embed.add_field(name="🚩 Country 🚩", value=data['vars'].get('locale', 'Unknown'), inline=True)
            
            # اللاعبين
            clients = data.get('clients', 0)
            max_clients = data.get('sv_maxclients', 0)
            embed.add_field(name="👤 Players 👤", value=f"{clients} / {max_clients}", inline=False)
            
            # روابط إضافية
            info_links = (
                f"/players.json: [Click Me](http://{ip}/players.json)\n"
                f"/info.json: [Click Me](http://{ip}/info.json)\n"
                f"/dynamic.json: [Click Me](http://{ip}/dynamic.json)"
            )
            embed.add_field(name="🔗 Other Information 🔗", value=info_links, inline=False)
            
            embed.set_footer(text="تم الفحص بواسطة بوت CFX العربي")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ عذراً، لم أستطع العثور على معلومات هذا السيرفر. تأكد من الكود.")
    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ تقني أثناء جلب البيانات.")

# --- 3. تشغيل البوت ---
if __name__ == "__main__":
    # تشغيل سيرفر الويب أولاً
    keep_alive()
    
    # جلب التوكن من Environment Variables في موقع Render
    # تأكد أنك سميت المتغير في Render باسم BOT_TOKEN
    token = os.environ.get('BOT_TOKEN')
    
    if token:
        bot.run(token)
    else:
        print("❌ خطأ: لم يتم العثور على BOT_TOKEN في إعدادات Render!")
