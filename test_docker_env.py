#!/usr/bin/env python3
"""
Comprehensive environment test script for Docker image.
Tests that all required dependencies are properly installed and functioning.
"""
import os
import sys
import logging
import importlib
import asyncio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("docker_env_test")

# Load environment variables
load_dotenv()

def check_dependency(module_name, package_name=None):
    """Check if a Python dependency is installed and importable"""
    package_name = package_name or module_name
    try:
        importlib.import_module(module_name)
        logger.info(f"✅ {package_name} is installed and importable")
        return True
    except ImportError as e:
        logger.error(f"❌ {package_name} is NOT installed: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = [
        "ANTHROPIC_API_KEY",
        "PERPLEXITY_API_KEY"
    ]
    
    # Check for either API key pattern
    bluefin_vars = []
    if os.getenv("BLUEFIN_PRIVATE_KEY"):
        bluefin_vars.append("BLUEFIN_PRIVATE_KEY")
        bluefin_vars.append("BLUEFIN_NETWORK")
    elif os.getenv("BLUEFIN_API_KEY") and os.getenv("BLUEFIN_API_SECRET"):
        bluefin_vars.append("BLUEFIN_API_KEY")
        bluefin_vars.append("BLUEFIN_API_SECRET")
    else:
        logger.warning("❌ No Bluefin credentials found")
    
    required_vars.extend(bluefin_vars)
    
    # Check all required vars
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            logger.error(f"❌ {var} environment variable is not set")
        else:
            # Don't print actual keys, just that they're set
            logger.info(f"✅ {var} environment variable is set")
    
    return len(missing_vars) == 0

async def check_playwright():
    """Check if Playwright is properly installed and functioning"""
    try:
        from playwright.async_api import async_playwright
        
        logger.info("✅ Playwright package is installed")
        
        # Try to launch a browser
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto("https://example.com")
                title = await page.title()
                logger.info(f"✅ Playwright browser launched successfully, got page title: {title}")
                await browser.close()
                return True
            except Exception as e:
                logger.error(f"❌ Error launching Playwright browser: {e}")
                return False
    except ImportError as e:
        logger.error(f"❌ Playwright is NOT installed: {e}")
        return False

def check_bluefin_libraries():
    """Check if Bluefin client libraries are installed and importable"""
    sui_available = False
    v2_available = False
    
    # Check SUI client
    try:
        from bluefin_client_sui import BluefinClient, Networks
        logger.info("✅ Bluefin SUI client library is installed")
        sui_available = True
    except ImportError as e:
        logger.warning(f"⚠️ Bluefin SUI client library is NOT installed: {e}")
    
    # Check V2 client
    try:
        from bluefin.v2.client import BluefinClient
        logger.info("✅ Bluefin V2 client library is installed")
        v2_available = True
    except ImportError as e:
        logger.warning(f"⚠️ Bluefin V2 client library is NOT installed: {e}")
    
    return sui_available or v2_available

async def check_anthropic():
    """Check if Anthropic API client is installed and functioning"""
    try:
        from anthropic import Client
        
        logger.info("✅ Anthropic client package is installed")
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("❌ ANTHROPIC_API_KEY not set")
            return False
        
        # Test basic API call
        try:
            client = Client(api_key=api_key)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Hello Claude! Please respond with only the words 'Docker test successful'."}
                ]
            )
            
            response_text = ""
            if hasattr(response, "content") and response.content:
                for content_block in response.content:
                    if hasattr(content_block, "text") and content_block.text:
                        response_text += content_block.text
            
            logger.info(f"✅ Anthropic API test successful. Response: {response_text}")
            return True
        except Exception as e:
            logger.error(f"❌ Anthropic API test failed: {e}")
            return False
    except ImportError as e:
        logger.error(f"❌ Anthropic client is NOT installed: {e}")
        return False

async def main():
    """Run all Docker environment tests"""
    logger.info("==== Starting Docker Environment Tests ====")
    
    # Check basic dependencies
    dependencies = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("dotenv", "python-dotenv"),
        ("anthropic", "Anthropic"),
        ("requests", "Requests"),
        ("backoff", "Backoff"),
        ("PIL", "Pillow")
    ]
    
    dependency_failures = 0
    for module, package in dependencies:
        if not check_dependency(module, package):
            dependency_failures += 1
    
    # Check environment variables
    env_check = check_environment_variables()
    
    # Check Bluefin libraries
    bluefin_check = check_bluefin_libraries()
    
    # Check Playwright
    playwright_check = await check_playwright()
    
    # Check Anthropic API
    anthropic_check = await check_anthropic()
    
    # Print summary
    logger.info("\n==== Test Summary ====")
    logger.info(f"Basic Dependencies: {'✅ PASS' if dependency_failures == 0 else f'❌ FAIL ({dependency_failures} missing)'}")
    logger.info(f"Environment Variables: {'✅ PASS' if env_check else '❌ FAIL'}")
    logger.info(f"Bluefin Libraries: {'✅ PASS' if bluefin_check else '❌ FAIL'}")
    logger.info(f"Playwright: {'✅ PASS' if playwright_check else '❌ FAIL'}")
    logger.info(f"Anthropic API: {'✅ PASS' if anthropic_check else '❌ FAIL'}")
    
    # Overall result
    if dependency_failures == 0 and env_check and bluefin_check and playwright_check and anthropic_check:
        logger.info("✅ ALL TESTS PASSED - Docker environment is properly configured")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED - Docker environment needs configuration")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result) 