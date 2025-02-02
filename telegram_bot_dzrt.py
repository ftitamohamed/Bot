import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from flask import Flask, request
import threading
import os

# URL of the page to monitor
url = 'https://www.dzrt.com/ar/our-products.html'  # Replace with the actual URL
# CSS selector for products
product_selector = '#layer-product-list > div.products.wrapper.grid.products-grid > ol > li'
BOT_TOKEN = '6746928562:AAEZ9oQAKRud8corKj5bLVtT7ScCw0FAxts'
# Replace 'YOUR_GROUP_CHAT_ID' with the chat ID of your group
GROUP_CHAT_ID = '-1002089332048'

async def send_message(bot, chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except TelegramError as e:
        print(f"Failed to send message: {e}")

def fetch_page(url):
    """Fetch the page content."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        return response
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

def parse_html(content):
    """Parse HTML content using BeautifulSoup."""
    return BeautifulSoup(content, 'html.parser')

def filter_elements_with_button(elements):
    """Filter elements that contain a button."""
    return [element for element in elements if element.find('button')]

def extract_product_names(elements):
    """Extract product names from the HTML elements."""
    product_names = []
    for product in elements:
        name_element = product.select_one('div.visible-front > strong > a')
        if name_element:
            product_names.append(name_element.get_text(strip=True))
    return product_names

async def check_availability(soup, bot):
    """Check product availability and extract available products."""
    products = soup.select(product_selector)

    # Filter elements that contain a button
    products_with_button = filter_elements_with_button(products)

    if products_with_button:
        message = "Product(s) are now available!"
        await send_message(bot, GROUP_CHAT_ID, message)
        print("Product(s) are now available!")
        product_names = extract_product_names(products_with_button)
        if product_names:
            print("Available Products:")
            for name in product_names:
                print(f"- {name}")
                await send_message(bot, GROUP_CHAT_ID, name)
        else:
            print("No product names found.")
    else:
        print("No products are available.")

async def scrape_page(url, bot):
    """Scrape the page and handle rate limits."""
    message = 'Welcome to dzrt watcher telegram bot'
    await send_message(bot, GROUP_CHAT_ID, message)
    response = fetch_page(url)
    if response:
        soup = parse_html(response.content)
        await check_availability(soup, bot)
    else:
        print("Failed to fetch the page.")

async def background_task():
    """Background task to run the scraper."""
    bot = Bot(token=BOT_TOKEN)
    while True:
        await scrape_page(url, bot)
        # Wait for 15 minutes before the next request
        wait_time = 15 * 60  # 15 minutes in seconds
        print(f"Waiting for {wait_time // 60} minutes before the next request.")
        message1 = f"Waiting for {wait_time // 60} minutes before the next request."
        await send_message(bot, GROUP_CHAT_ID, message1)
        await asyncio.sleep(wait_time)

def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(background_task())

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running"

if __name__ == "__main__":
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_background_loop, args=(new_loop,))
    t.start()

    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
