from sqlalchemy.orm import Session
from database import User, Portfolio, Transaction, UserPreferences, get_db
from typing import Dict, List, Optional
import json
from datetime import datetime

class PortfolioManager:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_portfolio(self, user_id: int) -> List[Dict]:
        """Get user's complete portfolio"""
        portfolios = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        return [
            {
                'id': p.id,
                'symbol': p.symbol,
                'quantity': p.quantity,
                'avg_price': p.avg_price,
                'current_value': p.current_value,
                'created_at': p.created_at,
                'updated_at': p.updated_at
            }
            for p in portfolios
        ]
    
    def add_position(self, user_id: int, symbol: str, quantity: float, price: float) -> bool:
        """Add or update a position in user's portfolio"""
        try:
            existing = self.db.query(Portfolio).filter(
                Portfolio.user_id == user_id,
                Portfolio.symbol == symbol
            ).first()
            
            if existing:
                # Update existing position
                total_cost = (existing.quantity * existing.avg_price) + (quantity * price)
                total_quantity = existing.quantity + quantity
                existing.avg_price = total_cost / total_quantity
                existing.quantity = total_quantity
                existing.current_value = total_quantity * price
                existing.updated_at = datetime.utcnow()
            else:
                # Create new position
                new_position = Portfolio(
                    user_id=user_id,
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=price,
                    current_value=quantity * price
                )
                self.db.add(new_position)
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"Error adding position: {e}")
            self.db.rollback()
            return False
    
    def remove_position(self, user_id: int, symbol: str, quantity: float, price: float) -> bool:
        """Remove or reduce a position in user's portfolio"""
        try:
            position = self.db.query(Portfolio).filter(
                Portfolio.user_id == user_id,
                Portfolio.symbol == symbol
            ).first()
            
            if not position:
                return False
            
            if position.quantity <= quantity:
                # Remove entire position
                self.db.delete(position)
            else:
                # Reduce position
                position.quantity -= quantity
                position.current_value = position.quantity * price
                position.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"Error removing position: {e}")
            self.db.rollback()
            return False
    
    def update_portfolio_values(self, user_id: int, market_prices: Dict[str, float]):
        """Update current values of all positions"""
        try:
            portfolios = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            
            for portfolio in portfolios:
                if portfolio.symbol in market_prices:
                    portfolio.current_value = portfolio.quantity * market_prices[portfolio.symbol]
                    portfolio.updated_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error updating portfolio values: {e}")
            self.db.rollback()
    
    def get_portfolio_summary(self, user_id: int) -> Dict:
        """Get portfolio summary with total value, P&L, etc."""
        portfolios = self.get_user_portfolio(user_id)
        
        total_value = sum(p['current_value'] for p in portfolios)
        total_cost = sum(p['quantity'] * p['avg_price'] for p in portfolios)
        total_pnl = total_value - total_cost
        pnl_percentage = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_positions': len(portfolios),
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pnl': total_pnl,
            'pnl_percentage': pnl_percentage,
            'positions': portfolios
        }

class TransactionManager:
    def __init__(self, db: Session):
        self.db = db
    
    def create_transaction(self, user_id: int, transaction_type: str, 
                         symbol: str = None, quantity: float = None, 
                         price: float = None, amount: float = None) -> Optional[int]:
        """Create a new transaction"""
        try:
            transaction = Transaction(
                user_id=user_id,
                type=transaction_type,
                symbol=symbol,
                quantity=quantity,
                price=price,
                amount=amount or (quantity * price if quantity and price else 0),
                status="pending"
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            return transaction.id
            
        except Exception as e:
            print(f"Error creating transaction: {e}")
            self.db.rollback()
            return None
    
    def complete_transaction(self, transaction_id: int) -> bool:
        """Mark transaction as completed"""
        try:
            transaction = self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
            if transaction:
                transaction.status = "completed"
                self.db.commit()
                return True
            return False
            
        except Exception as e:
            print(f"Error completing transaction: {e}")
            self.db.rollback()
            return False
    
    def get_user_transactions(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's transaction history"""
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()
        
        return [
            {
                'id': t.id,
                'type': t.type,
                'symbol': t.symbol,
                'quantity': t.quantity,
                'price': t.price,
                'amount': t.amount,
                'status': t.status,
                'created_at': t.created_at
            }
            for t in transactions
        ]

class UserManager:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_balance(self, user_id: int) -> float:
        """Get user's current balance"""
        user = self.db.query(User).filter(User.id == user_id).first()
        return user.balance if user else 0.0
    
    def update_balance(self, user_id: int, amount: float) -> bool:
        """Update user's balance"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.balance += amount
                self.db.commit()
                return True
            return False
            
        except Exception as e:
            print(f"Error updating balance: {e}")
            self.db.rollback()
            return False
    
    def withdraw_funds(self, user_id: int, amount: float) -> bool:
        """Withdraw funds from user account"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or user.balance < amount:
            return False
        
        try:
            # Create withdrawal transaction
            transaction_manager = TransactionManager(self.db)
            transaction_id = transaction_manager.create_transaction(
                user_id=user_id,
                transaction_type="withdraw",
                amount=amount
            )
            
            if transaction_id:
                # Update balance
                user.balance -= amount
                self.db.commit()
                
                # Complete transaction
                transaction_manager.complete_transaction(transaction_id)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error withdrawing funds: {e}")
            self.db.rollback()
            return False
    
    def deposit_funds(self, user_id: int, amount: float) -> bool:
        """Deposit funds to user account"""
        try:
            # Create deposit transaction
            transaction_manager = TransactionManager(self.db)
            transaction_id = transaction_manager.create_transaction(
                user_id=user_id,
                transaction_type="deposit",
                amount=amount
            )
            
            if transaction_id:
                # Update balance
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    user.balance += amount
                    self.db.commit()
                    
                    # Complete transaction
                    transaction_manager.complete_transaction(transaction_id)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error depositing funds: {e}")
            self.db.rollback()
            return False