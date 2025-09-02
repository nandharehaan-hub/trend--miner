import sqlite3
import json
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SimpleTrendMiner:
    def __init__(self, db_path: str = "trend_miner.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                balance REAL DEFAULT 1000.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Portfolio table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                quantity REAL,
                avg_price REAL,
                current_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                symbol TEXT,
                quantity REAL,
                price REAL,
                amount REAL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Trend analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                trend_score REAL,
                recommendation TEXT,
                confidence REAL,
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Simple password hashing"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, email: str, password: str) -> bool:
        """Register a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def login_user(self, username: str, password: str) -> Optional[Dict]:
        """Login user and return user data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute(
            "SELECT id, username, email, balance FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'balance': user[3]
            }
        return None
    
    def get_mock_market_data(self, symbol: str) -> Dict:
        """Generate mock market data for demonstration"""
        # Simulate realistic stock prices and movements
        base_prices = {
            'AAPL': 150, 'MSFT': 300, 'GOOGL': 120, 'TSLA': 200, 'AMZN': 100,
            'META': 250, 'NVDA': 400, 'SPY': 450, 'QQQ': 380, 'BTC-USD': 35000
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # Add some random variation
        price_variation = random.uniform(-0.1, 0.1)
        current_price = base_price * (1 + price_variation)
        
        # Calculate daily change
        daily_change = random.uniform(-0.05, 0.05)
        change_amount = current_price * daily_change
        
        return {
            'symbol': symbol,
            'price': round(current_price, 2),
            'change': round(change_amount, 2),
            'change_percent': round(daily_change * 100, 2),
            'volume': random.randint(1000000, 10000000),
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_trend(self, symbol: str) -> Dict:
        """Simple AI trend analysis simulation"""
        market_data = self.get_mock_market_data(symbol)
        
        # Simple trend analysis based on price change
        change_percent = market_data['change_percent']
        
        # Simulate more sophisticated analysis
        trend_factors = [
            random.uniform(-1, 1),  # Technical indicators
            random.uniform(-1, 1),  # Volume analysis
            random.uniform(-1, 1),  # Sentiment analysis
            change_percent / 5.0     # Price momentum
        ]
        
        trend_score = sum(trend_factors) / len(trend_factors)
        
        # Determine recommendation
        if trend_score > 0.3:
            recommendation = "buy"
        elif trend_score < -0.3:
            recommendation = "sell"
        else:
            recommendation = "hold"
        
        # Calculate confidence
        confidence = min(abs(trend_score) + 0.5, 0.95)
        
        analysis = {
            'symbol': symbol,
            'current_price': market_data['price'],
            'trend_score': round(trend_score, 3),
            'recommendation': recommendation,
            'confidence': round(confidence, 2),
            'change_percent': market_data['change_percent'],
            'analysis_time': datetime.now().isoformat(),
            'factors': {
                'technical': round(trend_factors[0], 2),
                'volume': round(trend_factors[1], 2),
                'sentiment': round(trend_factors[2], 2),
                'momentum': round(trend_factors[3], 2)
            }
        }
        
        # Store analysis in database
        self.store_analysis(analysis)
        
        return analysis
    
    def store_analysis(self, analysis: Dict):
        """Store trend analysis in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trend_analysis (symbol, trend_score, recommendation, confidence, analysis_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            analysis['symbol'],
            analysis['trend_score'],
            analysis['recommendation'],
            analysis['confidence'],
            json.dumps(analysis)
        ))
        
        conn.commit()
        conn.close()
    
    def invest(self, user_id: int, symbol: str, amount: float) -> bool:
        """Make an investment"""
        try:
            market_data = self.get_mock_market_data(symbol)
            price = market_data['price']
            quantity = amount / price
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check user balance
            cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
            balance = cursor.fetchone()[0]
            
            if balance < amount:
                conn.close()
                return False
            
            # Update balance
            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE id = ?",
                (amount, user_id)
            )
            
            # Add to portfolio
            cursor.execute('''
                INSERT OR REPLACE INTO portfolio (user_id, symbol, quantity, avg_price, current_value)
                VALUES (?, ?, 
                    COALESCE((SELECT quantity FROM portfolio WHERE user_id = ? AND symbol = ?), 0) + ?,
                    ?, ?)
            ''', (user_id, symbol, user_id, symbol, quantity, price, quantity * price))
            
            # Record transaction
            cursor.execute('''
                INSERT INTO transactions (user_id, type, symbol, quantity, price, amount)
                VALUES (?, 'buy', ?, ?, ?, ?)
            ''', (user_id, symbol, quantity, price, amount))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Investment error: {e}")
            return False
    
    def get_portfolio(self, user_id: int) -> List[Dict]:
        """Get user's portfolio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, quantity, avg_price, current_value
            FROM portfolio WHERE user_id = ? AND quantity > 0
        ''', (user_id,))
        
        positions = cursor.fetchall()
        conn.close()
        
        portfolio = []
        for pos in positions:
            # Update current value with latest price
            current_data = self.get_mock_market_data(pos[0])
            current_value = pos[1] * current_data['price']
            
            portfolio.append({
                'symbol': pos[0],
                'quantity': pos[1],
                'avg_price': pos[2],
                'current_price': current_data['price'],
                'current_value': round(current_value, 2),
                'pnl': round(current_value - (pos[1] * pos[2]), 2)
            })
        
        return portfolio
    
    def get_trending_stocks(self) -> List[str]:
        """Get list of trending stocks"""
        return ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'SPY', 'QQQ', 'BTC-USD']
    
    def auto_invest_recommendations(self, user_id: int, max_amount: float = 100.0) -> List[Dict]:
        """Get AI-powered investment recommendations"""
        trending = self.get_trending_stocks()
        recommendations = []
        
        for symbol in trending[:5]:  # Top 5 trending
            analysis = self.analyze_trend(symbol)
            
            if analysis['recommendation'] == 'buy' and analysis['confidence'] > 0.7:
                recommended_amount = min(max_amount, analysis['confidence'] * max_amount)
                recommendations.append({
                    'symbol': symbol,
                    'recommendation': analysis['recommendation'],
                    'confidence': analysis['confidence'],
                    'suggested_amount': round(recommended_amount, 2),
                    'current_price': analysis['current_price'],
                    'trend_score': analysis['trend_score']
                })
        
        return recommendations
    
    def withdraw_funds(self, user_id: int, amount: float) -> bool:
        """Withdraw funds from user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check balance
            cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
            balance = cursor.fetchone()[0]
            
            if balance < amount:
                conn.close()
                return False
            
            # Update balance
            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE id = ?",
                (amount, user_id)
            )
            
            # Record transaction
            cursor.execute('''
                INSERT INTO transactions (user_id, type, amount)
                VALUES (?, 'withdraw', ?)
            ''', (user_id, amount))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Withdrawal error: {e}")
            return False
    
    def deposit_funds(self, user_id: int, amount: float) -> bool:
        """Deposit funds to user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update balance
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE id = ?",
                (amount, user_id)
            )
            
            # Record transaction
            cursor.execute('''
                INSERT INTO transactions (user_id, type, amount)
                VALUES (?, 'deposit', ?)
            ''', (user_id, amount))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Deposit error: {e}")
            return False