import aiohttp
import xml.etree.ElementTree as ET
from typing import List
import urllib.parse

class DataScraper:
    """
    Data Fetcher to pull real RSS news headlines relevant to specific Kalshi markets.
    """
    def __init__(self):
        # We query Google News natively converting our Kalshi prompt into a safe URL
        self.rss_base = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def fetch_headlines(self, query: str) -> List[str]:
        """
        Asynchronously fetches XML headlines matching a market query using aiohttp.
        """
        # Convert the complex market question (e.g. "Will Bitcoin reach 100k") into keywords
        cleaned_query = query.replace("?", "").replace("Will", "").strip()
        encoded_query = urllib.parse.quote(cleaned_query)
        target_url = self.rss_base.format(query=encoded_query)
        
        headlines = []
        try:
            session = await self._get_session()
            async with session.get(target_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                        xml_content = await response.text()
                        root = ET.fromstring(xml_content)
                        # Extract the top 4 headlines from the RSS structure
                        for item in root.findall('./channel/item')[:4]:
                            title = item.find('title')
                            if title is not None and title.text:
                                headlines.append(title.text)
        except Exception as e:
            print(f"Error fetching RSS for {cleaned_query}: {e}")
            
        if not headlines:
            headlines.append(f"No breakthrough structural news recently surfaced regarding {cleaned_query}.")
            
        return headlines
