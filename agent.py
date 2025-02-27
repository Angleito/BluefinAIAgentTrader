from dotenv import load_dotenv
load_dotenv("/perpleixtytrader/.env/")
print("Loaded .env file")
from dotenv import load_dotenv
import os


# Access the OPENAI_API_KEY
openai_api_key = os.getenv("OPENAI_API_KEY")

# Use the API key to authenticate requests to OpenAI's API
print(f"Your OpenAI API Key is: {openai_api_key}")
import site
import sys
import getpass
from langchain_openai import ChatOpenAI
from browser_use import Agent, Controller
from langchain_openai.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_openai.llms import AzureOpenAI, OpenAI
import asyncio, time
from langchain.chat_models import init_chat_model
from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext
from playwright.sync_api import sync_playwright
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

ws_url = 'ws://68.96.160.135:2222/devtools/browser/934a6850-9b28-4811-a675-53b182220546'

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ws_url)  # Replace with actual IP and WebSocket URL

# Connect to existing browser
browser = Browser(
    config=BrowserConfig( 
        chrome_instance_path=r"/mnt/c\Users\Angle\Desktop\brave.exe - Shortcut.lnk",
    )
)

model = init_chat_model("gpt-4o-mini", model_provider="openai")


timestamp = int(time.time())


perplexity_prompt = f"""
type in https://www.perplexity.ai/finance at the top of the brave browser search url and read an artice about bitcoin. Then write a summary of the article in your own words. Next go search for TradingView.com and open a chart of SUI/USD with the source of PYTH, look at the indicators on the 4hour chart with heiken ashi and tell me if you should long or short on the next 4hour candle.
"""


async def main():
    agent = Agent(
        task=perplexity_prompt,
        llm=ChatOpenAI(model="gpt-4o"),
    )
    result = await agent.run()
    
    print(result)
		
asyncio.run(main())