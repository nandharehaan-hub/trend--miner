import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
import json

class DataFetcher:
    def __init__(self):
        self.popular_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'SPY', 'QQQ', 'IWM',
            'BTC-USD', 'ETH-USD', 'GOLD', 'GLD', 'TLT', 'VTI', 'VXUS', 'VEA', 'VWO', 'VOO'
        ]
        
    def get_realtime_data(self, symbol: str) -> Dict:
        """Get real-time data for a single symbol"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if data.empty:
                return None
                
            latest = data.iloc[-1]
            info = ticker.info
            
            return {
                'symbol': symbol,
                'price': float(latest['Close']),
                'volume': int(latest['Volume']),
                'change': float(latest['Close'] - data.iloc[0]['Open']),
                'change_percent': float((latest['Close'] - data.iloc[0]['Open']) / data.iloc[0]['Open'] * 100),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'timestamp': datetime.now(),
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'Unknown')
            }
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Get historical data for analysis"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_multiple_realtime_data(self, symbols: List[str]) -> List[Dict]:
        """Get real-time data for multiple symbols asynchronously"""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._async_get_data(symbol))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if r is not None and not isinstance(r, Exception)]
    
    async def _async_get_data(self, symbol: str) -> Dict:
        """Async wrapper for getting real-time data"""
        return self.get_realtime_data(symbol)
    
    def get_trending_symbols(self) -> List[str]:
        """Get list of trending symbols based on volume and price movement"""
        try:
            # For demo purposes, return popular symbols
            # In production, this would analyze volume spikes and price movements
            return self.popular_symbols
        except Exception as e:
            print(f"Error getting trending symbols: {e}")
            return self.popular_symbols
    
    def get_sector_data(self, sector: str) -> List[Dict]:
        """Get data for all stocks in a sector"""
        # Simplified sector mapping
        sector_symbols = {
            'technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA'],
            'finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS'],
            'healthcare': ['JNJ', 'PFE', 'UNH', 'MRK', 'ABBV'],
            'energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB'],
            'crypto': ['BTC-USD', 'ETH-USD']
        }
        
        symbols = sector_symbols.get(sector.lower(), self.popular_symbols[:5])
        return [self.get_realtime_data(symbol) for symbol in symbols]