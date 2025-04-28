### hk_weather_mcp_client.py
#!/usr/bin/env python

import asyncio
import json
import os
import sys
import logging
from contextlib import AsyncExitStack
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Check for API key
NOVA_ACT_API_KEY = os.getenv("NOVA_ACT_API_KEY")
if not NOVA_ACT_API_KEY:
    logger.error("NOVA_ACT_API_KEY environment variable not set")
    print("Error: NOVA_ACT_API_KEY environment variable not set")
    print("Please set it with: export NOVA_ACT_API_KEY=your_api_key")
    sys.exit(1)

class HKWeatherMCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server"""
        if not server_script_path.endswith(".py"):
            raise ValueError("Server script must be a .py file")

        logger.info(f"Connecting to server: {server_script_path}")

        # Set environment variables including the API key
        env = os.environ.copy()

        server_params = StdioServerParameters(
            command="python3", args=[server_script_path], env=env
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()
        logger.info("Connected to server and initialized session")

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        logger.info(f"Available tools: {[tool.name for tool in tools]}")
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    def extract_response_data(self, tool_response):
        """Extract response data from the tool response"""
        try:
            # Check if the response has content attribute
            if hasattr(tool_response, 'content') and tool_response.content:
                # Get the first TextContent object
                text_content = tool_response.content[0]
                # Extract the text and parse it as JSON
                if hasattr(text_content, 'text') and text_content.text:
                    return json.loads(text_content.text)

            # If we couldn't extract data using the above method, try other approaches
            if hasattr(tool_response, 'value'):
                return tool_response.value

            # If all else fails, return a default response
            return {"success": False, "error": "Could not extract response data"}
        except Exception as e:
            logger.error(f"Error extracting response data: {e}")
            return {"success": False, "error": str(e)}

    def format_forecast_data(self, forecast_data_json):
        """Format the forecast data in a readable way"""
        try:
            # Parse the nested JSON string
            forecast_data = json.loads(forecast_data_json)

            if "9-day_weather_forecast" in forecast_data:
                days = forecast_data["9-day_weather_forecast"]
                formatted_text = ""

                for day in days:
                    formatted_text += f"Date: {day['date']}\n"
                    formatted_text += f"Temperature: {day.get('daytime_temperature', 'N/A')}°C - {day.get('nighttime_temperature', 'N/A')}\n"
                    formatted_text += f"Humidity: {day.get('humidity', 'N/A')}\n"
                    formatted_text += f"Weather: {day.get('weather', 'N/A')} chance of rain\n"
                    formatted_text += "-" * 40 + "\n"

                return formatted_text
            else:
                return forecast_data_json
        except Exception as e:
            logger.error(f"Error formatting forecast data: {e}")
            return forecast_data_json

    async def process_query(self, query: str) -> str:
        """Process a query using direct tool calls"""
        try:
            logger.info(f"Processing query: {query}")

            # For current weather queries
            if "current" in query.lower() or "now" in query.lower() or "today" in query.lower():
                logger.info("Executing get_hk_current_weather tool")
                print("\nExecuting tool: get_hk_current_weather")
                tool_response = await self.session.call_tool(
                    "get_hk_current_weather",
                    {"headless": False, "take_screenshot": True}
                )
                logger.info("Tool call completed")

                # Extract response data
                response_data = self.extract_response_data(tool_response)
                logger.info(f"Extracted response data: {response_data}")

                if isinstance(response_data, dict) and response_data.get("success"):
                    weather_data = response_data.get("weather_data", "No weather data available")
                    screenshot_path = response_data.get("screenshot_path", "No screenshot available")

                    return f"""Current Weather in Hong Kong:

{weather_data}

A screenshot has been saved to: {screenshot_path}"""
                else:
                    error_msg = response_data.get("error", "") if isinstance(response_data, dict) else str(response_data)
                    return f"Error retrieving current weather: {error_msg}"

            # For forecast queries
            elif "forecast" in query.lower() or "week" in query.lower() or "days" in query.lower() or "tomorrow" in query.lower():
                logger.info("Executing get_hk_forecast tool")
                print("\nExecuting tool: get_hk_forecast")
                tool_response = await self.session.call_tool(
                    "get_hk_forecast",
                    {"headless": False, "take_screenshot": True}
                )
                logger.info("Tool call completed")

                # Extract response data
                response_data = self.extract_response_data(tool_response)
                logger.info(f"Extracted response data: {response_data}")

                if isinstance(response_data, dict) and response_data.get("success"):
                    forecast_data = response_data.get("forecast_data", "No forecast data available")
                    screenshot_path = response_data.get("screenshot_path", "No screenshot available")

                    # Format the forecast data
                    formatted_forecast = self.format_forecast_data(forecast_data)

                    return f"""9-Day Weather Forecast for Hong Kong:

{formatted_forecast}
A screenshot has been saved to: {screenshot_path}"""
                else:
                    error_msg = response_data.get("error", "") if isinstance(response_data, dict) else str(response_data)
                    return f"Error retrieving forecast: {error_msg}"

            # For warning queries
            elif "warning" in query.lower() or "alert" in query.lower():
                logger.info("Executing get_hk_weather_warnings tool")
                print("\nExecuting tool: get_hk_weather_warnings")
                tool_response = await self.session.call_tool(
                    "get_hk_weather_warnings",
                    {"headless": False, "take_screenshot": True}
                )
                logger.info("Tool call completed")

                # Extract response data
                response_data = self.extract_response_data(tool_response)
                logger.info(f"Extracted response data: {response_data}")

                if isinstance(response_data, dict) and response_data.get("success"):
                    warnings_data = response_data.get("warnings_data", "No warnings data available")
                    screenshot_path = response_data.get("screenshot_path", "No screenshot available")

                    return f"""Weather Warnings for Hong Kong:

{warnings_data}

A screenshot has been saved to: {screenshot_path}"""
                else:
                    error_msg = response_data.get("error", "") if isinstance(response_data, dict) else str(response_data)
                    return f"Error retrieving weather warnings: {error_msg}"

            # Default to current weather if query is unclear
            else:
                logger.info("Query unclear, defaulting to get_hk_current_weather tool")
                print("\nQuery unclear, defaulting to current weather")
                tool_response = await self.session.call_tool(
                    "get_hk_current_weather",
                    {"headless": False, "take_screenshot": True}
                )
                logger.info("Tool call completed")

                # Extract response data
                response_data = self.extract_response_data(tool_response)
                logger.info(f"Extracted response data: {response_data}")

                if isinstance(response_data, dict) and response_data.get("success"):
                    weather_data = response_data.get("weather_data", "No weather data available")

                    return f"""Current Weather in Hong Kong:

{weather_data}"""
                else:
                    error_msg = response_data.get("error", "") if isinstance(response_data, dict) else str(response_data)
                    return f"Error retrieving weather information: {error_msg}"

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"Error processing query: {str(e)}"

    async def close(self):
        """Close the client session"""
        logger.info("Closing client session")
        await self.exit_stack.aclose()

    async def interactive_session(self, server_script_path: str):
        """Run an interactive session with the user"""
        try:
            await self.connect_to_server(server_script_path)

            print("\n=== Hong Kong Weather Forecast Assistant ===")
            print("Type 'exit' or 'quit' to end the session")

            while True:
                query = input("\nWhat would you like to know about Hong Kong's weather? ")

                if query.lower() in ["exit", "quit"]:
                    logger.info("User requested to exit")
                    break

                print("\nProcessing your request...")
                response = await self.process_query(query)
                print("\n" + response)

        finally:
            await self.close()

async def main():
    """Main function to run the client"""
    if len(sys.argv) < 2:
        logger.error("Server script path not provided")
        print("Usage: python hk_weather_mcp_client.py <server_script_path>")
        sys.exit(1)

    server_script_path = sys.argv[1]
    logger.info(f"Starting client with server script: {server_script_path}")
    client = HKWeatherMCPClient()
    await client.interactive_session(server_script_path)

if __name__ == "__main__":
    asyncio.run(main())