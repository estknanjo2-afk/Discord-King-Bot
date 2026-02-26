import discord
from discord.ext import commands
import requests
from flask import Flask
from threading import Thread
import os

# --- 1. إنشاء سيرفر ويب بسيط لإبقاء البوت متصلاً ---
# هذا الجزء ضروري لأن Render يغلق البرامج التي لا تحتوي على رابط ويب (HTTP)
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

def run():
    # تشغيل السيرفر على البورت الذي يطلبه موقع Render
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. إعدادات بوت الديسكورد العربي ---
intents = discord.Intents.default()
intents.message_content = True  # تفعيل خاصية قراءة الرسائل للأوامر
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ تم تشغيل البوت بنجاح باسم: {bot.user}')

@bot.command()
async def فحص(ctx, link: str):
    """أمر فحص سيرفرات FiveM: !فحص [الرابط أو الكود]"""
    # استخراج كود السيرفر من نهاية الرابط
    server_code = link.split('/')[-1]
    
    # الرابط الرسمي لـ API الخاص بـ FiveM لجلب البيانات
    url = f"https://servers-frontend.fivem.net/api/servers/single/{server_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()['Data']
            
            # بناء الرسالة (Embed) بشكل احترافي يشبه طلبك الأصلي
            embed = discord.Embed(
                title=f"🌐 {data.get('hostname', 'سيرفر FiveM')[:50]}", 
                color=0x2b2d31
            )
            
            # استخراج الـ IP المباشر
            ip_address = data['connectEndPoints'][0]
            
            embed.add_field(name="💀 Server IP 💀", value=f"`{ip_address}`", inline=False)
            embed.add_field(name="⚠️ ISP ⚠️", value=data.get('ownerName', 'غير معروف'), inline=True)
            embed.add_field(name="🚩 Country 🚩", value=data['vars'].get('locale', 'Unknown'), inline=True)
            embed.add_field(name="👤 Players 👤", value=f"{data.get('clients', 0)} / {data.get('sv_maxclients', 0)}", inline=False)
            
            # روابط الملفات التقنية (JSON)
            json_links = (
                f"/players.json: [اضغط هنا](http://{ip_address}/players.json)\n"
                f"/info.json: [اضغط هنا](http://{ip_address}/info.json)\n"
                f"/dynamic.json: [اضغط هنا](http://{ip_address}/dynamic.json)"
            )
            embed.add_field(name="🔗 معلومات إضافية 🔗", value=json_links, inline=False)
            
            embed.set_footer(text="تم الفحص بواسطة King Bot")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ لم أتمكن من العثور على السيرفر، تأكد من صحة الرابط أو الكود.")
    except Exception as e:
        await ctx.send("⚠️ حدث خطأ تقني أثناء محاولة جلب البيانات.")

# --- 3. تشغيل النظام بالكامل ---
if __name__ == "__main__":
    # تشغيل سيرفر الويب في الخلفية
    keep_alive()
    
    # جلب التوكن من إعدادات Render (Environment Variables)
    # تأكد أنك أضفت متغير باسم BOT_TOKEN في موقع Render
    token = os.environ.get('BOT_TOKEN')
    
    if token:
        bot.run(token)
    else:
        print("❌ خطأ: لم يتم العثور على التوكن (BOT_TOKEN) في إعدادات الموقع!")
