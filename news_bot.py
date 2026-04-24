import asyncio
import json
import discord
from discord.ext import commands
from groq import Groq
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from pydantic import BaseModel, Field
from newspaper import Article
from typing import Optional
import feedparser
from typing import List
import random

# ==========================================
# CLASS 1: ĐỊNH NGHĨA FORM DỮ LIỆU (THE DATA MODEL)
# ==========================================
class NewsForm(BaseModel):
    """
    Class này đóng vai trò như một cái khuôn, đảm bảo mọi dữ liệu cào về
    đều phải tuân thủ đúng cấu trúc này trước khi chuyển cho AI.
    """
    title: str = Field(..., description="Tiêu đề bài báo")
    content: str = Field(..., description="Nội dung văn bản sạch")
    url: str = Field(..., description="Đường dẫn nguồn")

# ==========================================
# CLASS 2: XÁC ĐỊNH CÁC TRANG WEB CẦN CRAWL
# ==========================================
class NewsScout:
    """
    Class này chịu trách nhiệm đi tuần tra các trang RSS.
    Nếu thấy bài báo nào có chứa keyword, nó sẽ lấy URL đó về.
    """
    def __init__(self, rss_urls: List[str]):
        self.rss_urls = rss_urls

    def find_links_by_keywords(self, keywords: List[str]) -> List[str]:
        target_links = []
        for rss_url in self.rss_urls:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries:
                title = entry.title.lower()
                # Kiểm tra xem có keyword nào nằm trong tiêu đề không
                if any(kw.lower() in title for kw in keywords):
                    target_links.append(entry.link)
        
        # Trả về danh sách link không trùng lặp
        return list(set(target_links))

# ==========================================
# CLASS 3: BỘ CÀO DỮ LIỆU (THE CRAWLER)
# ==========================================
class NewsCrawler:
    def __init__(self, rss_urls: List[str]):
        self.browser_cfg = BrowserConfig(browser_type="chromium", headless=True)
        self.crawl_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        # Scout được khởi tạo bên trong Crawler
        self.scout = NewsScout(rss_urls=rss_urls)

    async def _fetch_single(self, url: str) -> Optional[NewsForm]:
        """Crawl 1 URL và trả về NewsForm"""
        try:
            async with AsyncWebCrawler(config=self.browser_cfg) as crawler:
                result = await crawler.arun(url=url, config=self.crawl_cfg)
                article = Article(url)
                article.download(input_html=result.html)
                article.parse()
                return NewsForm(
                    title=article.title,
                    content=article.text,
                    url=url
                )
        except Exception as e:
            print(f"❌ Lỗi khi crawl {url}: {e}")
            return None

    async def fetch_by_keywords(self, keywords: List[str]) -> List[NewsForm]:
        """Scout tìm link → Crawler crawl toàn bộ → trả List[NewsForm]"""
        links = self.scout.find_links_by_keywords(keywords)
        print(f"🔍 Scout tìm được {len(links)} link: {links}")

        results = []
        for url in links:
            news = await self._fetch_single(url)
            if news:
                results.append(news)
        return results

    async def fetch_single_url(self, url: str) -> Optional[NewsForm]:
        """Crawl thủ công 1 URL cụ thể (dùng cho !crawl)"""
        return await self._fetch_single(url)

# ==========================================
# CLASS 4: ĐẠI DIỆN DISCORD & AI (THE DISCORD AGENT)
# ==========================================
class DiscordAgent(commands.Bot):
    def __init__(self, user_token: str, groq_key: str, guild_id: int, channel_id: int, rss_urls: List[str], keywords: List[str]):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, self_bot=True)
        self.user_token = user_token
        self.groq_client = Groq(api_key=groq_key)
        self.target_guild_id = guild_id
        self.target_channel_id = channel_id
        self.keywords = keywords
        self.crawler = NewsCrawler(rss_urls=rss_urls)

    async def on_ready(self):
        print(f"--- ✅ Đặc vụ {self.user} đã sẵn sàng ---")
        print(f"--- 🎯 Guild: {self.target_guild_id} | Channel: {self.target_channel_id} ---")
        self.loop.create_task(self._news_loop())

    async def _think_with_groq(self, news_data: NewsForm) -> str:
        prompt = (
            "Bạn là một người dùng Discord bình thường, hài hước và hay hóng biến. "
            "Dựa trên dữ liệu JSON tin tức sau, hãy nhắn một tin vào group chat để kể cho bạn bè nghe. "
            "Yêu cầu: Ngôn ngữ Gen Z, dùng icon, không dùng tiêu đề bài báo kiểu trang trọng, "
            "hãy bắt đầu kiểu như 'Ê mấy ông ơi...', 'Vừa đọc được cái này...'. "
            "Tuyệt đối không được để lộ mình là AI."
        )
        completion = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Dữ liệu JSON: {news_data.model_dump_json()}"}
            ]
        )
        return completion.choices[0].message.content

    async def generate_by_keywords(self, keywords: List[str]) -> List[str]:
        news_list = await self.crawler.fetch_by_keywords(keywords)
        results = []
        for news in news_list:
            text = await self._think_with_groq(news)
            results.append(text)
        return results

    async def _news_loop(self):
        await self.wait_until_ready()

        # Kiểm tra guild hợp lệ
        guild = self.get_guild(self.target_guild_id)
        if not guild:
            print(f"❌ Không tìm thấy guild {self.target_guild_id}, dừng news loop.")
            return

        channel = self.get_channel(self.target_channel_id)
        if not channel:
            print(f"❌ Không tìm thấy channel {self.target_channel_id}, dừng news loop.")
            return

        while not self.is_closed():
            try:
                print("🔄 Bắt đầu pipeline tin tức...")
                messages = await self.generate_by_keywords(self.keywords)
                for msg in messages:
                    await channel.send(msg)
                    await asyncio.sleep(random.randint(30, 120))
                print(f"✅ Đã gửi {len(messages)} tin.")
            except Exception as e:
                print(f"❌ Lỗi news loop: {e}")

            interval = random.randint(3600, 10800)
            print(f"⏳ Nghỉ {interval//3} phút...")  # fix //0 → //60
            await asyncio.sleep(interval)