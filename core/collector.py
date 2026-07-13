import asyncio
import aiohttp
import logging
import numpy as np
from config import API_KEYS

logger = logging.getLogger('HYDRA.S3Collector')

class S3CausalCollector:
    def __init__(self):
        self.api_keys = API_KEYS
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def fetch_nasa_firms(self):
        url = f"https://firms.modaps.sos.nasa.gov/api/area/csv/{self.api_keys['nasa_firms']}/world/1/1"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    lines = text.strip().split('\n')
                    return len(lines) / 1000.0
                return 0.0
        except Exception as e:
            logger.error(f"NASA API Error: {e}")
            return 0.0

    async def fetch_eia_energy(self):
        url = f"https://api.eia.gov/v2/petroleum/pri/gs/data/?api_key={self.api_keys['eia']}"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    val = data['response']['data'][0]['value_f']
                    return (val / 100.0) % 1.0
                return 0.0
        except Exception as e:
            logger.error(f"EIA API Error: {e}")
            return 0.0

    async def fetch_openaq_industrial(self):
        url = "https://api.openaq.org/v2/latest?city=Beijing"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    val = data['results'][0]['measurements'][0]['value']
                    return (val / 500.0) % 1.0
                return 0.0
        except Exception as e:
            logger.error(f"OpenAQ API Error: {e}")
            return 0.0

    async def fetch_eth_liquidity(self):
        url = f"https://api.etherscan.io/api?module=account&action=bal&address=0x...&apikey={self.api_keys['etherscan']}"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return (int(data['result']) / 1e18) % 1.0
                return 0.0
        except Exception as e:
            logger.error(f"Etherscan API Error: {e}")
            return 0.0

    async def fetch_real_yield(self):
        """
        Surgical Truth: Fetching Real Yields via Yahoo Finance / Public CSV Proxy.
        We pull the 10-Year Treasury Real Rate (TIPS).
        """
        # Using a public financial data proxy (Yahoo Finance / Google Sheets export proxy)
        # For the most robust free version, we use a public CSV export from a trusted financial source.
        url = "https://fred.stlouisfed.org/graph/T10YIE" # Public page for 10-Year Real Interest Rate
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    # Basic parsing of the page to find the current value
                    import re
                    match = re.search(r'data-value="([-.\d]+)"', text)
                    if match:
                        val = float(match.group(1))
                        # Normalize: 0.0 is neutral, positive is contractionary, negative is expansionary
                        return (val + 5) / 10.0 # Normalizing -5% to 5% range to 0-1
                return 0.0
        except Exception as e:
            logger.error(f"RealYield API Error: {e}")
            return 0.0

    async def fetch_order_book_imbalance(self, symbol="PAXGUSDT"):
        """
        Surgical Truth: Fetching L2 Order Book Imbalance via Binance Public API.
        Pulls depth for the specified symbol to calculate OBI.
        """
        url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=10"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    bids = sum([float(b[1]) for b in data['bids']])
                    asks = sum([float(a[1]) for a in data['asks']])
                    # OBI formula: (Bids - Asks) / (Bids + Asks)
                    obi = (bids - asks) / (bids + asks)
                    return obi
                return 0.0
        except Exception as e:
            logger.error(f"OBI API Error for {symbol}: {e}")
            return 0.0

    async def collect_all_parallel(self, obi_symbol="PAXGUSDT"):
        tasks = [
            self.fetch_nasa_firms(),
            self.fetch_eia_energy(),
            self.fetch_openaq_industrial(),
            self.fetch_eth_liquidity(),
            self.fetch_real_yield(),
            self.fetch_order_book_imbalance(obi_symbol)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        processed = []
        for r in results:
            if isinstance(r, Exception) or r == 0.0:
                processed.append(None)
            else:
                processed.append(r)
        return {
            'NASA': processed[0], 'EIA': processed[1], 'OpenAQ': processed[2],
            'ETH': processed[3], 'RealYield': processed[4], 'OBI': processed[5]
        }
