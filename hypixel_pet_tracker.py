import requests
import pandas as pd
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from tkinter import Tk, Label, Button, Text, Scrollbar

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv('API_KEY')
BASE_URL = 'https://api.hypixel.net/skyblock/auctions'

CACHE_FILE = 'cache.json'
CACHE_DURATION = timedelta(hours=1)  # 1 hour cache duration

# Fetch all pages of auction data
def fetch_all_auction_data():
    print("Fetching new auction data from Hypixel API...")
    page = 0
    all_auctions = []

    while True:
        response = requests.get(f'{BASE_URL}?key={API_KEY}&page={page}')
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            break

        data = response.json()
        if 'auctions' not in data:
            break

        auctions = data['auctions']
        all_auctions.extend(auctions)
        page += 1

        if page >= data['totalPages']:  # Stop when all pages are fetched
            break

    # Cache the data
    with open(CACHE_FILE, 'w') as file:
        json.dump({'timestamp': datetime.now().isoformat(), 'data': all_auctions}, file)
        
    return all_auctions

# Load auction data with caching
def load_auction_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            cache = json.load(file)
            last_fetch = datetime.fromisoformat(cache['timestamp'])
            if datetime.now() - last_fetch < CACHE_DURATION:
                print("Using cached data.")
                return cache['data']
    
    # Fetch fresh data if cache is invalid or missing
    return fetch_all_auction_data()

# Extract pet price data
def get_pet_price_data(auctions):
    pet_prices = {}

    for auction in auctions:
        if auction.get('category') == 'pets':
            item_name = auction.get('item_name', '').lower()
            starting_bid = auction.get('starting_bid')

            # Identify Level 1 pets
            if 'lvl 1' in item_name:
                pet_name = item_name.split('lvl 1')[0].strip()
                if pet_name not in pet_prices:
                    pet_prices[pet_name] = {'lvl1': [], 'lvl100': []}
                pet_prices[pet_name]['lvl1'].append(starting_bid)

            # Identify Level 100 pets
            elif 'lvl 100' in item_name:
                pet_name = item_name.split('lvl 100')[0].strip()
                if pet_name not in pet_prices:
                    pet_prices[pet_name] = {'lvl1': [], 'lvl100': []}
                pet_prices[pet_name]['lvl100'].append(starting_bid)

    # Calculate min prices and net profit
    results = []
    for pet, prices in pet_prices.items():
        if prices['lvl1'] and prices['lvl100']:
            min_lvl1_price = min(prices['lvl1'])
            min_lvl100_price = min(prices['lvl100'])
            net_profit = min_lvl100_price - min_lvl1_price
            results.append((pet.capitalize(), min_lvl1_price, min_lvl100_price, net_profit))

    # Sort by highest net profit
    results.sort(key=lambda x: x[3], reverse=True)
    return results[:10]  # Return top 10 pets

# Display top 10 pets
def display_top_pets():
    auctions = load_auction_data()
    top_pets = get_pet_price_data(auctions)

    if not top_pets:
        print("No pets found for analysis.")
        return

    # Tkinter GUI
    root = Tk()
    root.title("Top 10 Pets to Level Up")
    root.geometry("600x400")

    Label(root, text="Top 10 Pets with Highest Net Profit", font=('Arial', 16)).pack(pady=10)
    text_area = Text(root, height=15, width=70, font=('Arial', 12))
    scrollbar = Scrollbar(root)
    scrollbar.pack(side="right", fill="y")
    text_area.pack()
    text_area.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=text_area.yview)

    # Display results
    text_area.insert("end", f"{'Pet':<20}{'Level 1 Price':<20}{'Level 100 Price':<20}{'Net Profit':<20}\n")
    text_area.insert("end", "=" * 80 + "\n")

    for pet, lvl1_price, lvl100_price, net_profit in top_pets:
        text_area.insert("end", f"{pet:<20}{lvl1_price:<20,}{lvl100_price:<20,}{net_profit:<20,}\n")

    Button(root, text="Close", command=root.quit, font=('Arial', 14)).pack(pady=10)
    root.mainloop()

if __name__ == '__main__':
    display_top_pets()
