from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import json
from datetime import datetime, timedelta

from database import init_db, get_db, User, UserPreferences
from auth import verify_password, get_password_hash, create_access_token, verify_token
from data_fetcher import DataFetcher
from ai_analyzer import AITrendAnalyzer
from portfolio_manager import PortfolioManager, TransactionManager, UserManager

# Initialize FastAPI app
app = FastAPI(title="AI-Powered Trend Miner", version="1.0.0")

# Security
security = HTTPBearer()

# Initialize components
data_fetcher = DataFetcher()
ai_analyzer = AITrendAnalyzer()

# Initialize database
init_db()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class InvestmentRequest(BaseModel):
    symbol: str
    amount: float

class WithdrawalRequest(BaseModel):
    amount: float

class PreferencesUpdate(BaseModel):
    risk_tolerance: str
    investment_amount: float
    auto_invest: bool
    preferred_sectors: List[str]
    preferred_symbols: List[str]

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                          db: Session = Depends(get_db)):
    username = verify_token(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        balance=1000.0  # Starting bonus
    )
    
    db.add(new_user)
    db.commit()
    
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    db_user = db.query(User).filter(User.username == user.username).first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "username": db_user.username,
        "balance": db_user.balance
    }

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get real-time market data for a symbol"""
    data = data_fetcher.get_realtime_data(symbol)
    if data is None:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return data

@app.get("/api/trending")
async def get_trending():
    """Get trending symbols"""
    symbols = data_fetcher.get_trending_symbols()
    trending_data = []
    
    for symbol in symbols[:10]:  # Top 10
        data = data_fetcher.get_realtime_data(symbol)
        if data:
            trending_data.append(data)
    
    return trending_data

@app.get("/api/analysis/{symbol}")
async def get_analysis(symbol: str):
    """Get AI trend analysis for a symbol"""
    analysis = ai_analyzer.analyze_trend(symbol)
    return analysis

@app.get("/api/portfolio")
async def get_portfolio(current_user: User = Depends(get_current_user), 
                       db: Session = Depends(get_db)):
    """Get user's portfolio"""
    portfolio_manager = PortfolioManager(db)
    return portfolio_manager.get_portfolio_summary(current_user.id)

@app.post("/api/invest")
async def invest(request: InvestmentRequest, 
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """Make an investment"""
    user_manager = UserManager(db)
    portfolio_manager = PortfolioManager(db)
    transaction_manager = TransactionManager(db)
    
    # Check if user has sufficient balance
    if current_user.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Get current price
    market_data = data_fetcher.get_realtime_data(request.symbol)
    if not market_data:
        raise HTTPException(status_code=404, detail="Symbol not found")
    
    price = market_data['price']
    quantity = request.amount / price
    
    # Create transaction
    transaction_id = transaction_manager.create_transaction(
        user_id=current_user.id,
        transaction_type="buy",
        symbol=request.symbol,
        quantity=quantity,
        price=price,
        amount=request.amount
    )
    
    if transaction_id:
        # Update balance
        if user_manager.update_balance(current_user.id, -request.amount):
            # Add to portfolio
            if portfolio_manager.add_position(current_user.id, request.symbol, quantity, price):
                # Complete transaction
                transaction_manager.complete_transaction(transaction_id)
                return {"message": "Investment successful", "transaction_id": transaction_id}
    
    raise HTTPException(status_code=500, detail="Investment failed")

@app.post("/api/sell")
async def sell(request: InvestmentRequest,
              current_user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """Sell an investment"""
    user_manager = UserManager(db)
    portfolio_manager = PortfolioManager(db)
    transaction_manager = TransactionManager(db)
    
    # Get current price
    market_data = data_fetcher.get_realtime_data(request.symbol)
    if not market_data:
        raise HTTPException(status_code=404, detail="Symbol not found")
    
    price = market_data['price']
    quantity = request.amount / price
    
    # Create transaction
    transaction_id = transaction_manager.create_transaction(
        user_id=current_user.id,
        transaction_type="sell",
        symbol=request.symbol,
        quantity=quantity,
        price=price,
        amount=request.amount
    )
    
    if transaction_id:
        # Remove from portfolio
        if portfolio_manager.remove_position(current_user.id, request.symbol, quantity, price):
            # Update balance
            if user_manager.update_balance(current_user.id, request.amount):
                # Complete transaction
                transaction_manager.complete_transaction(transaction_id)
                return {"message": "Sale successful", "transaction_id": transaction_id}
    
    raise HTTPException(status_code=500, detail="Sale failed")

@app.post("/api/withdraw")
async def withdraw(request: WithdrawalRequest,
                  current_user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """Withdraw funds"""
    user_manager = UserManager(db)
    
    if user_manager.withdraw_funds(current_user.id, request.amount):
        return {"message": "Withdrawal successful", "amount": request.amount}
    else:
        raise HTTPException(status_code=400, detail="Withdrawal failed - insufficient balance")

@app.post("/api/deposit")
async def deposit(request: WithdrawalRequest,  # Same model, just different endpoint
                 current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """Deposit funds (simulated for demo)"""
    user_manager = UserManager(db)
    
    if user_manager.deposit_funds(current_user.id, request.amount):
        return {"message": "Deposit successful", "amount": request.amount}
    else:
        raise HTTPException(status_code=500, detail="Deposit failed")

@app.get("/api/transactions")
async def get_transactions(current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    """Get user's transaction history"""
    transaction_manager = TransactionManager(db)
    return transaction_manager.get_user_transactions(current_user.id)

@app.put("/api/preferences")
async def update_preferences(prefs: PreferencesUpdate,
                           current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    """Update user preferences"""
    user_prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    if user_prefs:
        user_prefs.risk_tolerance = prefs.risk_tolerance
        user_prefs.investment_amount = prefs.investment_amount
        user_prefs.auto_invest = prefs.auto_invest
        user_prefs.preferred_sectors = json.dumps(prefs.preferred_sectors)
        user_prefs.preferred_symbols = json.dumps(prefs.preferred_symbols)
        user_prefs.updated_at = datetime.utcnow()
    else:
        user_prefs = UserPreferences(
            user_id=current_user.id,
            risk_tolerance=prefs.risk_tolerance,
            investment_amount=prefs.investment_amount,
            auto_invest=prefs.auto_invest,
            preferred_sectors=json.dumps(prefs.preferred_sectors),
            preferred_symbols=json.dumps(prefs.preferred_symbols)
        )
        db.add(user_prefs)
    
    db.commit()
    return {"message": "Preferences updated successfully"}

@app.get("/api/preferences")
async def get_preferences(current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """Get user preferences"""
    user_prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    if user_prefs:
        return {
            "risk_tolerance": user_prefs.risk_tolerance,
            "investment_amount": user_prefs.investment_amount,
            "auto_invest": user_prefs.auto_invest,
            "preferred_sectors": json.loads(user_prefs.preferred_sectors or "[]"),
            "preferred_symbols": json.loads(user_prefs.preferred_symbols or "[]")
        }
    
    return {
        "risk_tolerance": "medium",
        "investment_amount": 100.0,
        "auto_invest": False,
        "preferred_sectors": [],
        "preferred_symbols": []
    }

@app.get("/api/user")
async def get_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "balance": current_user.balance,
        "created_at": current_user.created_at
    }

# Background task for auto-investing
async def auto_invest_task():
    """Background task to handle auto-investing based on AI recommendations"""
    while True:
        try:
            db = next(get_db())
            
            # Get users with auto-invest enabled
            auto_invest_users = db.query(User).join(UserPreferences).filter(
                UserPreferences.auto_invest == True
            ).all()
            
            for user in auto_invest_users:
                user_prefs = db.query(UserPreferences).filter(
                    UserPreferences.user_id == user.id
                ).first()
                
                if user_prefs and user.balance >= user_prefs.investment_amount:
                    # Get preferred symbols or use trending
                    symbols = json.loads(user_prefs.preferred_symbols or "[]")
                    if not symbols:
                        symbols = data_fetcher.get_trending_symbols()[:5]
                    
                    # Analyze trends and invest in best opportunities
                    for symbol in symbols:
                        analysis = ai_analyzer.analyze_trend(symbol)
                        
                        if (analysis['recommendation'] == 'buy' and 
                            analysis['confidence'] > 0.7):
                            
                            # Make automatic investment
                            portfolio_manager = PortfolioManager(db)
                            user_manager = UserManager(db)
                            transaction_manager = TransactionManager(db)
                            
                            market_data = data_fetcher.get_realtime_data(symbol)
                            if market_data:
                                amount = min(user_prefs.investment_amount, user.balance)
                                price = market_data['price']
                                quantity = amount / price
                                
                                # Create and execute transaction
                                transaction_id = transaction_manager.create_transaction(
                                    user_id=user.id,
                                    transaction_type="buy",
                                    symbol=symbol,
                                    quantity=quantity,
                                    price=price,
                                    amount=amount
                                )
                                
                                if transaction_id:
                                    if user_manager.update_balance(user.id, -amount):
                                        if portfolio_manager.add_position(user.id, symbol, quantity, price):
                                            transaction_manager.complete_transaction(transaction_id)
                                            
                                            # Break after one investment per cycle
                                            break
            
            db.close()
            
        except Exception as e:
            print(f"Auto-invest task error: {e}")
        
        # Wait 5 minutes before next cycle
        await asyncio.sleep(300)

# Start background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_invest_task())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)