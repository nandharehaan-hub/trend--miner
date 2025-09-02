// Global variables
let currentUser = null;
let authToken = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
});

// Authentication functions
function checkAuthStatus() {
    const token = localStorage.getItem('authToken');
    if (token) {
        authToken = token;
        getCurrentUser();
    } else {
        showWelcome();
    }
}

async function getCurrentUser() {
    try {
        const response = await fetch('/api/user', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            currentUser = await response.json();
            showDashboard();
            loadDashboardData();
        } else {
            localStorage.removeItem('authToken');
            showWelcome();
        }
    } catch (error) {
        console.error('Error getting user:', error);
        showWelcome();
    }
}

function showLogin() {
    document.getElementById('authModalTitle').textContent = 'Login';
    document.getElementById('emailField').style.display = 'none';
    document.getElementById('authSubmit').textContent = 'Login';
    document.getElementById('authForm').onsubmit = handleLogin;
    new bootstrap.Modal(document.getElementById('authModal')).show();
}

function showRegister() {
    document.getElementById('authModalTitle').textContent = 'Register';
    document.getElementById('emailField').style.display = 'block';
    document.getElementById('authSubmit').textContent = 'Register';
    document.getElementById('authForm').onsubmit = handleRegister;
    new bootstrap.Modal(document.getElementById('authModal')).show();
}

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            currentUser = {
                id: data.user_id,
                username: data.username,
                balance: data.balance
            };
            
            bootstrap.Modal.getInstance(document.getElementById('authModal')).hide();
            showDashboard();
            loadDashboardData();
        } else {
            showAlert(data.detail || 'Login failed', 'danger');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('Login failed', 'danger');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert('Registration successful! Please login.', 'success');
            bootstrap.Modal.getInstance(document.getElementById('authModal')).hide();
            setTimeout(showLogin, 1000);
        } else {
            showAlert(data.detail || 'Registration failed', 'danger');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showAlert('Registration failed', 'danger');
    }
}

function logout() {
    localStorage.removeItem('authToken');
    authToken = null;
    currentUser = null;
    showWelcome();
}

// UI functions
function showWelcome() {
    document.getElementById('welcome').style.display = 'block';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('user-info').style.display = 'none';
    document.getElementById('auth-buttons').style.display = 'block';
}

function showDashboard() {
    document.getElementById('welcome').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('user-info').style.display = 'block';
    document.getElementById('auth-buttons').style.display = 'none';
    
    if (currentUser) {
        document.getElementById('balance').textContent = currentUser.balance.toFixed(2);
    }
}

// Dashboard functions
async function loadDashboardData() {
    await Promise.all([
        loadTrendingStocks(),
        loadPortfolio(),
        loadTransactions()
    ]);
}

async function loadTrendingStocks() {
    try {
        const response = await fetch('/api/trending');
        const trending = await response.json();
        
        const container = document.getElementById('trending-stocks');
        container.innerHTML = '';
        
        for (const stock of trending) {
            // Get AI analysis for each stock
            const analysisResponse = await fetch(`/api/analysis/${stock.symbol}`);
            const analysis = await analysisResponse.json();
            
            const card = createTrendingCard(stock, analysis);
            container.appendChild(card);
        }
    } catch (error) {
        console.error('Error loading trending stocks:', error);
    }
}

function createTrendingCard(stock, analysis) {
    const div = document.createElement('div');
    div.className = 'col-lg-4 col-md-6 mb-3';
    
    const changeClass = stock.change >= 0 ? 'positive' : 'negative';
    const changeIcon = stock.change >= 0 ? '↗' : '↘';
    
    div.innerHTML = `
        <div class="trending-card">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">${stock.symbol}</h6>
                <span class="recommendation-${analysis.recommendation}">${analysis.recommendation.toUpperCase()}</span>
            </div>
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="h5 mb-0">$${stock.price.toFixed(2)}</span>
                <span class="${changeClass}">
                    ${changeIcon} ${stock.change_percent.toFixed(2)}%
                </span>
            </div>
            <div class="mb-2">
                <small class="text-muted">AI Confidence:</small>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${(analysis.confidence * 100).toFixed(0)}%"></div>
                </div>
                <small class="text-muted">${(analysis.confidence * 100).toFixed(0)}%</small>
            </div>
            <button class="btn btn-primary btn-sm w-100" onclick="showInvestmentModal('${stock.symbol}')">
                Trade
            </button>
        </div>
    `;
    
    return div;
}

async function loadPortfolio() {
    try {
        const response = await fetch('/api/portfolio', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const portfolio = await response.json();
            
            // Update summary cards
            document.getElementById('portfolio-value').textContent = `$${portfolio.total_value.toFixed(2)}`;
            document.getElementById('portfolio-pnl').textContent = `$${portfolio.total_pnl.toFixed(2)}`;
            document.getElementById('portfolio-positions').textContent = portfolio.total_positions;
            document.getElementById('available-balance').textContent = `$${currentUser.balance.toFixed(2)}`;
            
            // Update portfolio table
            const tbody = document.getElementById('portfolio-table');
            tbody.innerHTML = '';
            
            portfolio.positions.forEach(position => {
                const row = document.createElement('tr');
                const pnl = position.current_value - (position.quantity * position.avg_price);
                const pnlClass = pnl >= 0 ? 'positive' : 'negative';
                
                row.innerHTML = `
                    <td>${position.symbol}</td>
                    <td>${position.quantity.toFixed(4)}</td>
                    <td>$${position.avg_price.toFixed(2)}</td>
                    <td>$${position.current_value.toFixed(2)}</td>
                    <td class="${pnlClass}">$${pnl.toFixed(2)}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="showInvestmentModal('${position.symbol}', 'sell')">
                            Sell
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error loading portfolio:', error);
    }
}

async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const transactions = await response.json();
            
            const tbody = document.getElementById('transactions-table');
            tbody.innerHTML = '';
            
            transactions.forEach(transaction => {
                const row = document.createElement('tr');
                const date = new Date(transaction.created_at).toLocaleDateString();
                
                row.innerHTML = `
                    <td>${date}</td>
                    <td>${transaction.type.toUpperCase()}</td>
                    <td>${transaction.symbol || '-'}</td>
                    <td>${transaction.quantity ? transaction.quantity.toFixed(4) : '-'}</td>
                    <td>${transaction.price ? '$' + transaction.price.toFixed(2) : '-'}</td>
                    <td>$${transaction.amount.toFixed(2)}</td>
                    <td>
                        <span class="badge bg-${transaction.status === 'completed' ? 'success' : 'warning'}">
                            ${transaction.status}
                        </span>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

// Investment functions
function showInvestmentModal(symbol, action = 'buy') {
    document.getElementById('investSymbol').value = symbol;
    document.getElementById('investAction').value = action;
    document.getElementById('investmentModalTitle').textContent = action === 'buy' ? 'Buy Stock' : 'Sell Stock';
    
    new bootstrap.Modal(document.getElementById('investmentModal')).show();
}

document.getElementById('investmentForm').onsubmit = async function(event) {
    event.preventDefault();
    
    const symbol = document.getElementById('investSymbol').value;
    const amount = parseFloat(document.getElementById('investAmount').value);
    const action = document.getElementById('investAction').value;
    
    try {
        const endpoint = action === 'buy' ? '/api/invest' : '/api/sell';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ symbol, amount })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(`${action === 'buy' ? 'Investment' : 'Sale'} successful!`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('investmentModal')).hide();
            refreshData();
        } else {
            showAlert(data.detail || `${action} failed`, 'danger');
        }
    } catch (error) {
        console.error(`${action} error:`, error);
        showAlert(`${action} failed`, 'danger');
    }
};

// Utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.insertBefore(alertDiv, document.body.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

async function refreshData() {
    if (currentUser) {
        await getCurrentUser();
        await loadDashboardData();
    }
}

// Placeholder functions for modals
function showDepositModal() {
    // Simplified deposit - just add $1000 for demo
    fetch('/api/deposit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ amount: 1000 })
    }).then(response => {
        if (response.ok) {
            showAlert('$1000 deposited successfully!', 'success');
            refreshData();
        }
    });
}

function showWithdrawModal() {
    const amount = prompt('Enter withdrawal amount:');
    if (amount && !isNaN(amount)) {
        fetch('/api/withdraw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ amount: parseFloat(amount) })
        }).then(response => response.json()).then(data => {
            if (data.message) {
                showAlert(data.message, 'success');
                refreshData();
            } else {
                showAlert('Withdrawal failed', 'danger');
            }
        });
    }
}

function showPreferencesModal() {
    showAlert('Preferences modal coming soon!', 'info');
}