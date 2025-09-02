#!/usr/bin/env python3
"""
AI-Powered Trend Miner Demo
A simple command-line interface for the trend mining system
"""

from simple_trend_miner import SimpleTrendMiner
import json

def print_header():
    print("=" * 60)
    print("🚀 AI-POWERED TREND MINER")
    print("💰 Make Money in Your Sleep")
    print("=" * 60)

def print_menu():
    print("\n📋 Main Menu:")
    print("1. 👤 Register/Login")
    print("2. 📊 View Market Trends")
    print("3. 🔍 Analyze Stock")
    print("4. 💵 Invest")
    print("5. 📈 View Portfolio")
    print("6. 🤖 AI Recommendations")
    print("7. 💳 Deposit Funds")
    print("8. 💸 Withdraw Funds")
    print("9. ❌ Exit")

def main():
    trend_miner = SimpleTrendMiner()
    current_user = None
    
    print_header()
    
    while True:
        print_menu()
        choice = input("\n🎯 Select option (1-9): ").strip()
        
        if choice == "1":
            # Register/Login
            print("\n🔐 Authentication")
            action = input("(R)egister or (L)ogin? ").strip().upper()
            
            if action == "R":
                print("\n📝 Registration")
                username = input("Username: ")
                email = input("Email: ")
                password = input("Password: ")
                
                if trend_miner.register_user(username, email, password):
                    print("✅ Registration successful!")
                else:
                    print("❌ Registration failed - user might already exist")
            
            elif action == "L":
                print("\n🔑 Login")
                username = input("Username: ")
                password = input("Password: ")
                
                user = trend_miner.login_user(username, password)
                if user:
                    current_user = user
                    print(f"✅ Welcome back, {user['username']}!")
                    print(f"💰 Balance: ${user['balance']:.2f}")
                else:
                    print("❌ Invalid credentials")
        
        elif choice == "2":
            # View Market Trends
            print("\n📊 TRENDING STOCKS")
            print("-" * 40)
            trending = trend_miner.get_trending_stocks()
            
            for symbol in trending:
                data = trend_miner.get_mock_market_data(symbol)
                change_indicator = "📈" if data['change_percent'] > 0 else "📉"
                print(f"{change_indicator} {symbol}: ${data['price']:.2f} "
                      f"({data['change_percent']:+.2f}%)")
        
        elif choice == "3":
            # Analyze Stock
            symbol = input("\n🔍 Enter stock symbol to analyze: ").strip().upper()
            if symbol:
                print(f"\n🤖 AI Analysis for {symbol}")
                print("-" * 40)
                
                analysis = trend_miner.analyze_trend(symbol)
                
                print(f"💰 Current Price: ${analysis['current_price']:.2f}")
                print(f"📊 Trend Score: {analysis['trend_score']:.3f}")
                print(f"🎯 Recommendation: {analysis['recommendation'].upper()}")
                print(f"🎲 Confidence: {analysis['confidence']:.1%}")
                print(f"📈 Daily Change: {analysis['change_percent']:+.2f}%")
                
                print("\n🔬 Analysis Factors:")
                for factor, value in analysis['factors'].items():
                    indicator = "📈" if value > 0 else "📉"
                    print(f"  {indicator} {factor.title()}: {value:+.2f}")
        
        elif choice == "4":
            # Invest
            if not current_user:
                print("❌ Please login first")
                continue
                
            symbol = input("\n💵 Enter stock symbol to invest in: ").strip().upper()
            try:
                amount = float(input("💰 Enter investment amount: $"))
                
                if trend_miner.invest(current_user['id'], symbol, amount):
                    print(f"✅ Successfully invested ${amount:.2f} in {symbol}!")
                    # Update user balance
                    current_user['balance'] -= amount
                else:
                    print("❌ Investment failed - insufficient balance")
            except ValueError:
                print("❌ Invalid amount")
        
        elif choice == "5":
            # View Portfolio
            if not current_user:
                print("❌ Please login first")
                continue
                
            print(f"\n📈 PORTFOLIO - {current_user['username']}")
            print("-" * 50)
            
            portfolio = trend_miner.get_portfolio(current_user['id'])
            
            if not portfolio:
                print("📭 No positions found")
            else:
                total_value = 0
                total_pnl = 0
                
                for pos in portfolio:
                    pnl_indicator = "💚" if pos['pnl'] >= 0 else "💔"
                    print(f"{pnl_indicator} {pos['symbol']}: {pos['quantity']:.4f} shares")
                    print(f"   💰 Value: ${pos['current_value']:.2f}")
                    print(f"   📊 P&L: {pos['pnl']:+.2f}")
                    print()
                    
                    total_value += pos['current_value']
                    total_pnl += pos['pnl']
                
                print(f"💼 Total Portfolio Value: ${total_value:.2f}")
                print(f"📊 Total P&L: {total_pnl:+.2f}")
        
        elif choice == "6":
            # AI Recommendations
            if not current_user:
                print("❌ Please login first")
                continue
                
            print("\n🤖 AI INVESTMENT RECOMMENDATIONS")
            print("-" * 50)
            
            recommendations = trend_miner.auto_invest_recommendations(current_user['id'])
            
            if not recommendations:
                print("📭 No strong buy signals found at the moment")
            else:
                for rec in recommendations:
                    print(f"🎯 {rec['symbol']}")
                    print(f"   💰 Price: ${rec['current_price']:.2f}")
                    print(f"   🎲 Confidence: {rec['confidence']:.1%}")
                    print(f"   💵 Suggested Amount: ${rec['suggested_amount']:.2f}")
                    print(f"   📊 Trend Score: {rec['trend_score']:+.3f}")
                    print()
                
                auto_invest = input("🤖 Execute AI recommendations? (y/n): ").strip().lower()
                if auto_invest == 'y':
                    for rec in recommendations:
                        if trend_miner.invest(current_user['id'], rec['symbol'], rec['suggested_amount']):
                            print(f"✅ Auto-invested ${rec['suggested_amount']:.2f} in {rec['symbol']}")
                            current_user['balance'] -= rec['suggested_amount']
                        else:
                            print(f"❌ Failed to invest in {rec['symbol']}")
        
        elif choice == "7":
            # Deposit Funds
            if not current_user:
                print("❌ Please login first")
                continue
                
            try:
                amount = float(input("\n💳 Enter deposit amount: $"))
                if trend_miner.deposit_funds(current_user['id'], amount):
                    print(f"✅ Successfully deposited ${amount:.2f}!")
                    current_user['balance'] += amount
                else:
                    print("❌ Deposit failed")
            except ValueError:
                print("❌ Invalid amount")
        
        elif choice == "8":
            # Withdraw Funds
            if not current_user:
                print("❌ Please login first")
                continue
                
            try:
                amount = float(input("\n💸 Enter withdrawal amount: $"))
                if trend_miner.withdraw_funds(current_user['id'], amount):
                    print(f"✅ Successfully withdrew ${amount:.2f}!")
                    current_user['balance'] -= amount
                else:
                    print("❌ Withdrawal failed - insufficient balance")
            except ValueError:
                print("❌ Invalid amount")
        
        elif choice == "9":
            print("\n👋 Thank you for using AI-Powered Trend Miner!")
            print("💰 Keep making money in your sleep! 🚀")
            break
        
        else:
            print("❌ Invalid option. Please select 1-9.")
        
        if current_user:
            print(f"\n💰 Current Balance: ${current_user['balance']:.2f}")

if __name__ == "__main__":
    main()