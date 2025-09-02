import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple
import json
from datetime import datetime, timedelta
from data_fetcher import DataFetcher

class AITrendAnalyzer:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.scaler = StandardScaler()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for trend analysis"""
        if data.empty:
            return data
            
        # Simple Moving Averages
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        data['EMA_12'] = data['Close'].ewm(span=12).mean()
        data['EMA_26'] = data['Close'].ewm(span=26).mean()
        
        # MACD
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_signal'] = data['MACD'].ewm(span=9).mean()
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        data['BB_middle'] = data['Close'].rolling(window=20).mean()
        bb_std = data['Close'].rolling(window=20).std()
        data['BB_upper'] = data['BB_middle'] + (bb_std * 2)
        data['BB_lower'] = data['BB_middle'] - (bb_std * 2)
        
        # Volume indicators
        data['Volume_MA'] = data['Volume'].rolling(window=20).mean()
        data['Volume_ratio'] = data['Volume'] / data['Volume_MA']
        
        # Price momentum
        data['Price_momentum'] = data['Close'].pct_change(periods=5)
        data['Price_volatility'] = data['Close'].rolling(window=20).std()
        
        return data
    
    def prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for ML model"""
        if data.empty:
            return np.array([])
            
        features = [
            'SMA_10', 'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26',
            'MACD', 'MACD_signal', 'RSI', 'BB_upper', 'BB_lower',
            'Volume_ratio', 'Price_momentum', 'Price_volatility'
        ]
        
        feature_data = data[features].dropna()
        
        if feature_data.empty:
            return np.array([])
            
        return feature_data.values
    
    def train_model(self, symbol: str):
        """Train the AI model with historical data"""
        try:
            # Get more historical data for training
            historical_data = self.data_fetcher.get_historical_data(symbol, "2y")
            
            if historical_data.empty:
                return False
                
            # Calculate technical indicators
            data_with_indicators = self.calculate_technical_indicators(historical_data)
            
            # Prepare features and targets
            features = self.prepare_features(data_with_indicators)
            
            if len(features) == 0:
                return False
                
            # Target: future price movement (5 days ahead)
            data_with_indicators['Future_return'] = data_with_indicators['Close'].shift(-5).pct_change(periods=1)
            targets = data_with_indicators['Future_return'].dropna().values
            
            # Align features and targets
            min_length = min(len(features), len(targets))
            features = features[:min_length]
            targets = targets[:min_length]
            
            if len(features) < 50:  # Need minimum data points
                return False
                
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Train model
            self.model.fit(features_scaled, targets)
            self.is_trained = True
            
            return True
            
        except Exception as e:
            print(f"Error training model for {symbol}: {e}")
            return False
    
    def analyze_trend(self, symbol: str) -> Dict:
        """Analyze trend for a given symbol"""
        try:
            # Get historical data
            historical_data = self.data_fetcher.get_historical_data(symbol, "6mo")
            
            if historical_data.empty:
                return self._fallback_analysis(symbol)
                
            # Calculate technical indicators
            data_with_indicators = self.calculate_technical_indicators(historical_data)
            
            # Get latest data point
            latest_data = data_with_indicators.iloc[-1]
            
            # Calculate trend signals
            trend_signals = self._calculate_trend_signals(data_with_indicators)
            
            # AI prediction if model is trained
            ai_prediction = 0
            confidence = 0.5
            
            if self.is_trained:
                features = self.prepare_features(data_with_indicators)
                if len(features) > 0:
                    latest_features = features[-1].reshape(1, -1)
                    features_scaled = self.scaler.transform(latest_features)
                    ai_prediction = self.model.predict(features_scaled)[0]
                    confidence = min(abs(ai_prediction) * 10, 0.95)  # Scale confidence
            
            # Combine signals for final recommendation
            final_score = self._combine_signals(trend_signals, ai_prediction)
            recommendation = self._get_recommendation(final_score)
            
            return {
                'symbol': symbol,
                'trend_score': final_score,
                'recommendation': recommendation,
                'confidence': confidence,
                'signals': trend_signals,
                'ai_prediction': ai_prediction,
                'current_price': float(latest_data['Close']),
                'rsi': float(latest_data['RSI']) if not pd.isna(latest_data['RSI']) else 50,
                'macd': float(latest_data['MACD']) if not pd.isna(latest_data['MACD']) else 0,
                'volume_signal': trend_signals.get('volume_signal', 0),
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing trend for {symbol}: {e}")
            return self._fallback_analysis(symbol)
    
    def _calculate_trend_signals(self, data: pd.DataFrame) -> Dict:
        """Calculate various trend signals"""
        latest = data.iloc[-1]
        
        signals = {}
        
        # Moving average signals
        if not pd.isna(latest['SMA_10']) and not pd.isna(latest['SMA_20']):
            signals['ma_signal'] = 1 if latest['SMA_10'] > latest['SMA_20'] else -1
        else:
            signals['ma_signal'] = 0
            
        # MACD signal
        if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_signal']):
            signals['macd_signal'] = 1 if latest['MACD'] > latest['MACD_signal'] else -1
        else:
            signals['macd_signal'] = 0
            
        # RSI signal
        if not pd.isna(latest['RSI']):
            if latest['RSI'] < 30:
                signals['rsi_signal'] = 1  # Oversold, potential buy
            elif latest['RSI'] > 70:
                signals['rsi_signal'] = -1  # Overbought, potential sell
            else:
                signals['rsi_signal'] = 0
        else:
            signals['rsi_signal'] = 0
            
        # Volume signal
        if not pd.isna(latest['Volume_ratio']):
            signals['volume_signal'] = 1 if latest['Volume_ratio'] > 1.5 else 0
        else:
            signals['volume_signal'] = 0
            
        # Price momentum signal
        if not pd.isna(latest['Price_momentum']):
            signals['momentum_signal'] = 1 if latest['Price_momentum'] > 0.02 else (-1 if latest['Price_momentum'] < -0.02 else 0)
        else:
            signals['momentum_signal'] = 0
            
        return signals
    
    def _combine_signals(self, signals: Dict, ai_prediction: float) -> float:
        """Combine all signals into a final trend score"""
        # Weight the signals
        weights = {
            'ma_signal': 0.2,
            'macd_signal': 0.2,
            'rsi_signal': 0.15,
            'volume_signal': 0.15,
            'momentum_signal': 0.15,
            'ai_prediction': 0.15
        }
        
        total_score = 0
        for signal, value in signals.items():
            total_score += value * weights.get(signal, 0)
            
        # Add AI prediction
        total_score += ai_prediction * weights['ai_prediction']
        
        # Normalize to -1 to 1 range
        return max(-1, min(1, total_score))
    
    def _get_recommendation(self, score: float) -> str:
        """Convert trend score to recommendation"""
        if score > 0.3:
            return "buy"
        elif score < -0.3:
            return "sell"
        else:
            return "hold"
    
    def _fallback_analysis(self, symbol: str) -> Dict:
        """Fallback analysis when data is insufficient"""
        current_data = self.data_fetcher.get_realtime_data(symbol)
        
        if current_data:
            # Simple analysis based on daily change
            change_percent = current_data['change_percent']
            
            if change_percent > 2:
                recommendation = "buy"
                score = 0.5
            elif change_percent < -2:
                recommendation = "sell"
                score = -0.5
            else:
                recommendation = "hold"
                score = 0
                
            return {
                'symbol': symbol,
                'trend_score': score,
                'recommendation': recommendation,
                'confidence': 0.3,
                'current_price': current_data['price'],
                'change_percent': change_percent,
                'analysis_time': datetime.now().isoformat(),
                'note': 'Simplified analysis due to insufficient data'
            }
        
        return {
            'symbol': symbol,
            'trend_score': 0,
            'recommendation': "hold",
            'confidence': 0.1,
            'analysis_time': datetime.now().isoformat(),
            'note': 'No data available'
        }