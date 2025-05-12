### hk_weather_mcp_server.py
#!/usr/bin/env python

import asyncio
import json
import os
import tempfile
import threading
import uuid
import logging
import traceback
import concurrent.futures
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from nova_act import ActError, NovaAct

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("hk-weather-forecast-server")

# Global variables for session management and results storage
results_store = {}
results_lock = threading.Lock()
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Helper functions
def generate_id(prefix: str) -> str:
    """Generate a unique ID for results"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def capture_screenshot(nova_act, name="screenshot"):
    """Take a screenshot and save it to a temporary file"""
    try:
        temp_dir = tempfile.gettempdir()
        screenshot_path = os.path.join(temp_dir, f"{name}_{uuid.uuid4().hex[:8]}.png")
        nova_act.page.screenshot(path=screenshot_path)
        return {"screenshot_path": screenshot_path, "success": True}
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return {"error": str(e), "success": False}

def run_nova_act_current_weather(headless=False, take_screenshot=True):
    """Run NovaAct to get current weather in a separate thread"""
    try:
        logger.info("Starting NovaAct for current weather in thread")
        with NovaAct(
            starting_page="https://www.hko.gov.hk/en/wxinfo/currwx/current.htm",
            headless=headless,
        ) as nova_act:
            logger.info("NovaAct instance created successfully")
            result = nova_act.act("Read and extract the current weather information for Hong Kong including temperature, humidity, and weather conditions")
            logger.info(f"Act command completed. Response: {result.response}")

            screenshot_result = None
            if take_screenshot:
                logger.info("Taking screenshot...")
                screenshot_result = capture_screenshot(nova_act, "hk_current_weather")
                logger.info(f"Screenshot taken: {screenshot_result}")

            return {
                "success": True,
                "message": "Successfully retrieved current weather in Hong Kong",
                "weather_data": result.response,
                "screenshot_path": screenshot_result.get("screenshot_path") if screenshot_result else None,
            }
    except Exception as e:
        logger.error(f"Error in run_nova_act_current_weather: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error retrieving current weather: {str(e)}",
            "error": str(e),
        }

def run_nova_act_forecast(days=9, headless=False, take_screenshot=True):
    """Run NovaAct to get forecast in a separate thread"""
    try:
        logger.info("Starting NovaAct for forecast in thread")
        with NovaAct(
            starting_page="https://www.hko.gov.hk/en/wxinfo/currwx/fnd.htm",
            headless=headless,
        ) as nova_act:
            logger.info("NovaAct instance created successfully")
            result = nova_act.act("Read and extract the complete 9-day weather forecast information visible on this page")
            logger.info(f"Act command completed. Response: {result.response}")

            screenshot_result = None
            if take_screenshot:
                logger.info("Taking screenshot...")
                screenshot_result = capture_screenshot(nova_act, "hk_forecast")
                logger.info(f"Screenshot taken: {screenshot_result}")

            return {
                "success": True,
                "message": f"Successfully retrieved {days}-day forecast for Hong Kong",
                "forecast_data": result.response,
                "screenshot_path": screenshot_result.get("screenshot_path") if screenshot_result else None,
            }
    except Exception as e:
        logger.error(f"Error in run_nova_act_forecast: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error retrieving forecast: {str(e)}",
            "error": str(e),
        }

def run_nova_act_warnings(headless=False, take_screenshot=True):
    """Run NovaAct to get weather warnings in a separate thread"""
    try:
        logger.info("Starting NovaAct for weather warnings in thread")
        with NovaAct(
            starting_page="https://www.hko.gov.hk/en/wxinfo/currwx/warning.htm",
            headless=headless,
        ) as nova_act:
            logger.info("NovaAct instance created successfully")
            result = nova_act.act("Read and extract any current weather warnings or alerts for Hong Kong")
            logger.info(f"Act command completed. Response: {result.response}")

            screenshot_result = None
            if take_screenshot:
                logger.info("Taking screenshot...")
                screenshot_result = capture_screenshot(nova_act, "hk_warnings")
                logger.info(f"Screenshot taken: {screenshot_result}")

            return {
                "success": True,
                "message": "Successfully retrieved weather warnings for Hong Kong",
                "warnings_data": result.response,
                "screenshot_path": screenshot_result.get("screenshot_path") if screenshot_result else None,
            }
    except Exception as e:
        logger.error(f"Error in run_nova_act_warnings: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error retrieving weather warnings: {str(e)}",
            "error": str(e),
        }

# MCP tools
@mcp.tool()
async def get_hk_current_weather(headless: bool = False, take_screenshot: bool = True) -> Dict[str, Any]:
    """Get the current weather in Hong Kong from the Hong Kong Observatory website.

    Args:
        headless: Whether to run the browser in headless mode. Default is False.
        take_screenshot: Whether to take a screenshot of the weather information. Default is True.
    """
    try:
        logger.info("Starting get_hk_current_weather tool...")
        logger.info(f"Parameters: headless={headless}, take_screenshot={take_screenshot}")

        # Run NovaAct in a separate thread
        future = thread_pool.submit(run_nova_act_current_weather, headless, take_screenshot)
        result = future.result()

        logger.info(f"Thread completed. Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in get_hk_current_weather: {str(e)}")
        logger.error(traceback.format_exc())
        error_data = {
            "success": False,
            "message": f"Error retrieving current weather: {str(e)}",
            "error": str(e),
        }
        logger.error(f"Returning error response: {error_data}")
        return error_data

@mcp.tool()
async def get_hk_forecast(days: int = 9, headless: bool = False, take_screenshot: bool = True) -> Dict[str, Any]:
    """Get the weather forecast for Hong Kong from the Hong Kong Observatory website.

    Args:
        days: Number of days to forecast (up to 9). Default is 9.
        headless: Whether to run the browser in headless mode. Default is False.
        take_screenshot: Whether to take a screenshot of the forecast. Default is True.
    """
    try:
        logger.info("Starting get_hk_forecast tool...")
        logger.info(f"Parameters: days={days}, headless={headless}, take_screenshot={take_screenshot}")

        # Run NovaAct in a separate thread
        future = thread_pool.submit(run_nova_act_forecast, days, headless, take_screenshot)
        result = future.result()

        logger.info(f"Thread completed. Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in get_hk_forecast: {str(e)}")
        logger.error(traceback.format_exc())
        error_data = {
            "success": False,
            "message": f"Error retrieving forecast: {str(e)}",
            "error": str(e),
        }
        logger.error(f"Returning error response: {error_data}")
        return error_data

@mcp.tool()
async def get_hk_weather_warnings(headless: bool = False, take_screenshot: bool = True) -> Dict[str, Any]:
    """Get current weather warnings and alerts for Hong Kong.

    Args:
        headless: Whether to run the browser in headless mode. Default is False.
        take_screenshot: Whether to take a screenshot of the warnings. Default is True.
    """
    try:
        logger.info("Starting get_hk_weather_warnings tool...")
        logger.info(f"Parameters: headless={headless}, take_screenshot={take_screenshot}")

        # Run NovaAct in a separate thread
        future = thread_pool.submit(run_nova_act_warnings, headless, take_screenshot)
        result = future.result()

        logger.info(f"Thread completed. Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in get_hk_weather_warnings: {str(e)}")
        logger.error(traceback.format_exc())
        error_data = {
            "success": False,
            "message": f"Error retrieving weather warnings: {str(e)}",
            "error": str(e),
        }
        logger.error(f"Returning error response: {error_data}")
        return error_data

# Run the server
if __name__ == "__main__":
    logger.info("Starting HK Weather MCP Server...")
    mcp.run()