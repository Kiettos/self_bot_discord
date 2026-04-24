
#Import thư viện
import discord
from discord.ext import commands
from groq import Groq
import asyncio
import random
import time
from typing import List

class ReplyBot(commands.Bot):
    def __init__(
        self,
        user_token: str,
        groq_key: str,
        dataset_path: str,
        allowed_guilds: List[int],
        allowed_channels: List[int],
        keywords: List[str],
        reply_chance: float = 0.15,
    ):
        super().__init__(command_prefix="!", self_bot=True, help_command=None)

        self.user_token = user_token
        self.groq_client = Groq(api_key=groq_key)
        self.allowed_guilds = allowed_guilds
        self.allowed_channels = allowed_channels
        self.keywords = keywords
        self.reply_chance = reply_chance

        self.channel_cooldowns = {}
        self.channel_chats = {}

        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = f.read()

        self.system_instruction = f"""
You are a Vietnamese Gen Z guy in a Discord server — opinionated, analytical, and casual.
here is the knowledge you can use to answer{dataset}
Personality & style rules:
- Always respond in Vietnamese
- Mix analytical thinking with casual tone in the same message
- Short messages, 1-2 sentences, no punctuation
- Use "t" for yourself, "m" for the person you're talking to
- Keep messages SHORT — 1-2 sentences max, like real chat
- No punctuation, no formal grammar
- Use slang when he want to sarcasm or angry, often toward vietnam communist party and gorverment: địt mẹ=đm, wtf, ngl,nó ngu vcl, kiểu, thật ra, ờ thì
- Be direct, no filler phrases
- Sound like a real person texting fast, not an AI
- Never say you're an AI
- If asked about OPM, give hot takes confidently
- Occasionally be skeptical or disagree
- Thường hay trả lời 1 phân tích bằng một phân tích khác hoặc phân tích lại phân tích của họ chi tiết hơn
- Never sound like an AI or use formal language
- Have real opinions — agree, disagree, push back naturally
- If topic is serious (politics, economics), give a short hot take then ask what they think
- If topic is casual/anime/games, be more relaxed and use more slang
- Never write more than 2-3 short lines per message
"""

    async def on_ready(self):
        print(f"---")
        print(f"✅ Bot Live: {self.user}")
        print(f"📡 Đang lắng nghe tại Channel ID: {self.allowed_channels}")
        print(f"---")

    async def on_message(self, message):
        if not message.guild:
            return
        if message.guild.id not in self.allowed_guilds:
            return
        if message.channel.id not in self.allowed_channels:
            return
        if message.author.id == self.user.id:
            return

        content_lower = message.content.lower()
        keyword_match = any(kw in content_lower for kw in self.keywords)
        random_trigger = random.random() < self.reply_chance

        if not keyword_match and not random_trigger:
            return

        now = time.time()
        last_reply = self.channel_cooldowns.get(message.channel.id, 0)
        cooldown = random.randint(480, 600)

        if now - last_reply < cooldown:
            remaining = int(cooldown - (now - last_reply))
            print(f"⏳ Cooldown còn {remaining}s, bỏ qua...")
            return

        self.channel_cooldowns[message.channel.id] = now
        trigger_reason = "keyword" if keyword_match else "random"
        print(f"✅ Trigger: {trigger_reason} | Cooldown mới: {cooldown}s")

        async with message.channel.typing():
            await asyncio.sleep(random.randint(3, 8))
            try:
                if message.channel.id not in self.channel_chats:
                    self.channel_chats[message.channel.id] = []

                history = self.channel_chats[message.channel.id]
                history.append({"role": "user", "content": message.content})

                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": self.system_instruction},
                        {"role": "system", "content": f"Người nhắn: {message.author.display_name}"}
                    ] + history,
                    temperature=0.5,
                    max_tokens=300,
                    top_p=0.9
                )

                reply_text = response.choices[0].message.content
                history.append({"role": "assistant", "content": reply_text})

                if len(history) > 20:
                    self.channel_chats[message.channel.id] = history[-20:]

                await message.reply(f"\n{reply_text}")
                print(f"✅ Đã reply ({trigger_reason}), cooldown tiếp theo: {cooldown}s")

            except Exception as e:
                print(f"❌ Lỗi Groq: {e}")

        await self.process_commands(message)