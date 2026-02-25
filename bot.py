import discord
from discord import app_commands
import google.generativeai as genai
import edge_tts
import os
from flask import Flask
from threading import Thread

# خادم ويب للبقاء حياً على Render
app = Flask('')
@app.route('/')
def home():
    return "King is Alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# جلب المفاتيح من النظام
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_KEY')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

RULES = "1. الاحترام متبادل. 2. يمنع السب. 3. يمنع التخريب."

class KingBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = KingBot()

@bot.tree.command(name='king', description='اسأل الملك')
async def king(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    vc = interaction.guild.voice_client
    if not vc and interaction.user.voice:
        vc = await interaction.user.voice.channel.connect()
    elif not vc:
        await interaction.followup.send("ادخل روم صوتي!")
        return

    response = model.generate_content(f"أنت ملك، القوانين: {RULES}. أجب باختصار: {question}")
    answer = response.text
    await interaction.followup.send(f"**الملك:** {answer}")
    
    communicate = edge_tts.Communicate(answer, 'ar-SA-ZariyahNeural')
    await communicate.save('king.mp3')
    vc.play(discord.FFmpegPCMAudio('king.mp3'))

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
