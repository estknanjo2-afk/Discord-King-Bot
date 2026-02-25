import discord
from discord import app_commands
import google.generativeai as genai
import edge_tts
import os
from flask import Flask
from threading import Thread

# --- إعداد خادم ويب لإبقاء البوت نشطاً على Render ---
app = Flask('')
@app.route('/')
def home():
    return "الملك حيّ ويرزق!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- جلب المفاتيح من إعدادات البيئة الآمنة (Environment) ---
# تأكد أنك وضعتهم في Render كما في صورتك السابقة
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_KEY')

# إعداد ذكاء Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# قوانين الديوان الملكي
RULES = "1. الاحترام متبادل. 2. يمنع السب. 3. يمنع التخريب."

class KingBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # مزامنة الأوامر مع سيرفرات ديسكورد
        await self.tree.sync()
        print("تمت مزامنة الأوامر الملكية بنجاح!")

bot = KingBot()

@bot.event
async def on_ready():
    print(f'الملك {bot.user} استلم العرش على Render!')

@bot.tree.command(name='king', description='اسأل الملك وسيقوم بالرد عليك صوتياً')
async def king(interaction: discord.Interaction, question: str):
    # أهم سطر: يخبر ديسكورد أن البوت "يفكر" لمنع رسالة الخطأ
    await interaction.response.defer(thinking=True)
    
    # التحقق من وجود المستخدم في روم صوتي
    vc = interaction.guild.voice_client
    if not vc:
        if interaction.user.voice:
            vc = await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("يا مواطن، يجب أن تكون في روم صوتي لأسمعك!")
            return

    try:
        # توليد الرد عبر جيمناي
        prompt = f"أنت ملك حكيم. القوانين هي: {RULES}. أجب بفخامة وقصر: {question}"
        response = model.generate_content(prompt)
        answer = response.text
        
        # تحويل النص لخطاب ملكي صوتي
        communicate = edge_tts.Communicate(answer, 'ar-SA-ZariyahNeural')
        await communicate.save('king.mp3')
        
        # إرسال الرد النصي ثم تشغيل الصوت
        await interaction.followup.send(f"**خطاب ملكي:** {answer}")
        
        # تشغيل الصوت (تأكد من وجود ffmpeg على السيرفر)
        if vc and vc.is_connected():
            vc.play(discord.FFmpegPCMAudio('king.mp3'))
            
    except Exception as e:
        print(f"Error: {e}")
        await interaction.followup.send("عذراً، حدث اضطراب في الديوان الملكي.")

# تشغيل البوت
if __name__ == "__main__":
    keep_alive()
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("خطأ: لم يتم العثور على DISCORD_TOKEN في الإعدادات!")
