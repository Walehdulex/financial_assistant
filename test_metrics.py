import requests
import time
from random import choice

BASE_URL = "http://localhost:5000"
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
portfolio_ids = [1, 2, 3]  # Replace with actual IDs
user_id = 1  # Replace with actual user ID

# Login first to get a session
session = requests.Session()
session.post(f"{BASE_URL}/login", data={
    "email": "your_test_user@example.com",
    "password": "your_password"
})

# Generate stock data requests (some will hit cache, some won't)
print("Testing market data API...")
for _ in range(20):
    symbol = choice(symbols)
    session.get(f"{BASE_URL}/api/stock/{symbol}")
    time.sleep(0.5)

# Generate portfolio page views
print("Testing portfolio pages...")
for _ in range(10):
    portfolio_id = choice(portfolio_ids)
    session.get(f"{BASE_URL}/portfolio/details/{portfolio_id}")
    session.get(f"{BASE_URL}/portfolio/performance/{portfolio_id}")
    session.get(f"{BASE_URL}/portfolio/risk/{portfolio_id}")
    time.sleep(1)

# Run benchmarks
print("Running benchmarks...")
for portfolio_id in portfolio_ids:
    session.get(f"{BASE_URL}/admin/run-benchmarks/{portfolio_id}/{user_id}")
    time.sleep(2)

print("Done! Check metrics dashboard.")