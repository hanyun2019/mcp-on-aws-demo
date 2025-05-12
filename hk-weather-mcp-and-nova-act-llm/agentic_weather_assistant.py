#!/usr/bin/env python

import asyncio
import json
import os
import sys
import logging
from contextlib import AsyncExitStack
from typing import Optional, Dict, Any, List

import boto3
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

# Initialize Bedrock client
try:
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-west-2",  # Change to your preferred region
    )
    logger.info("Bedrock client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Bedrock client: {e}")
    print(f"Error initializing Bedrock client: {e}")
    print("Please ensure you have AWS credentials configured correctly")
    sys.exit(1)

class AgenticWeatherAssistant:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"  # Change to your preferred model
        self.system_prompt = """
        You are a helpful weather assistant for Hong Kong. You can provide current weather information, 
        forecasts, and weather warnings by using the available tools. When responding:
        
        1. Be concise and informative
        2. Focus on the weather information requested
        3. Interpret the data from the tools to provide insights
        4. Suggest appropriate actions based on weather conditions when relevant
        5. If you don't have enough information, use the appropriate tool to get it
        
        Available tools:
        - get_hk_current_weather: Get current weather conditions in Hong Kong
        - get_hk_forecast: Get the 9-day weather forecast for Hong Kong
        - get_hk_weather_warnings: Get any active weather warnings for Hong Kong
        """

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
        
        # Store tool schemas for later use
        self.available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in tools
        ]

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

    async def process_query_with_llm(self, query: str) -> str:
        """Process a query using Bedrock LLM and available tools"""
        try:
            logger.info(f"Processing query with LLM: {query}")
            
            if not self.available_tools:
                return "No tools available on the server."

            # Prepare messages and tools for Bedrock
            messages = [{"role": "user", "content": [{"text": query}]}]

            # Format tools for Bedrock
            tool_list = [
                {
                    "toolSpec": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "inputSchema": {"json": tool["input_schema"]},
                    }
                }
                for tool in self.available_tools
            ]

            # Generate conversation with Bedrock
            try:
                # Make the API call to Bedrock
                response = bedrock_runtime.converse(
                    modelId=self.model_id,
                    messages=messages,
                    inferenceConfig={"temperature": 0.7},
                    toolConfig={"tools": tool_list},
                    system=[{"text": self.system_prompt}],
                )

                # Process the response
                final_responses = []
                response_message = response["output"]["message"]

                # Process each content block in the response
                for content_block in response_message["content"]:
                    if "text" in content_block:
                        # Add text responses to our final output
                        final_responses.append(content_block["text"])

                    elif "toolUse" in content_block:
                        # Handle tool usage
                        tool_use = content_block["toolUse"]
                        tool_name = tool_use["name"]
                        tool_input = tool_use["input"]
                        tool_use_id = tool_use["toolUseId"]

                        print(f"Calling tool: {tool_name} with input: {tool_input}")
                        final_responses.append(f"[Calling tool {tool_name}]")

                        # Call the tool through MCP session
                        tool_result = await self.session.call_tool(tool_name, tool_input)

                        # Extract the content from the tool result
                        result_content = self.extract_response_data(tool_result)
                        
                        # Format the result for Bedrock
                        if isinstance(result_content, dict) and "success" in result_content:
                            if result_content["success"]:
                                # Extract the relevant data based on the tool
                                if tool_name == "get_hk_current_weather":
                                    result_for_bedrock = {
                                        "result": result_content.get("weather_data", "No weather data available"),
                                        "screenshot": result_content.get("screenshot_path", "No screenshot available")
                                    }
                                elif tool_name == "get_hk_forecast":
                                    result_for_bedrock = {
                                        "result": result_content.get("forecast_data", "No forecast data available"),
                                        "screenshot": result_content.get("screenshot_path", "No screenshot available")
                                    }
                                elif tool_name == "get_hk_weather_warnings":
                                    result_for_bedrock = {
                                        "result": result_content.get("warnings_data", "No warnings data available"),
                                        "screenshot": result_content.get("screenshot_path", "No screenshot available")
                                    }
                                else:
                                    result_for_bedrock = {"result": result_content}
                            else:
                                result_for_bedrock = {"error": result_content.get("error", "Unknown error")}
                        else:
                            result_for_bedrock = {"result": result_content}

                        # Create follow-up message with tool result
                        tool_result_message = {
                            "role": "user",
                            "content": [
                                {
                                    "toolResult": {
                                        "toolUseId": tool_use_id,
                                        "content": [{"json": result_for_bedrock}],
                                    }
                                }
                            ],
                        }

                        # Add the AI message and tool result to messages
                        messages.append(response_message)
                        messages.append(tool_result_message)

                        # Make another call to get the final response
                        follow_up_response = bedrock_runtime.converse(
                            modelId=self.model_id,
                            messages=messages,
                            inferenceConfig={"temperature": 0.7},
                            toolConfig={"tools": tool_list},
                            system=[{"text": self.system_prompt}],
                        )

                        # Add the follow-up response to our final output
                        follow_up_text = follow_up_response["output"]["message"]["content"][0]["text"]
                        final_responses.append(follow_up_text)

                return "\n".join(final_responses)

            except Exception as e:
                logger.error(f"Error in Bedrock API call: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Fall back to direct tool calling if Bedrock fails
                logger.info("Falling back to direct tool calling")
                return await self.process_query_direct(query)

        except Exception as e:
            logger.error(f"Error processing query with LLM: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"Error processing query: {str(e)}"

    async def process_query_direct(self, query: str) -> str:
        """Process a query using direct tool calls (fallback method)"""
        try:
            logger.info(f"Processing query directly: {query}")

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

                    return f"""9-Day Weather Forecast for Hong Kong:

{forecast_data}

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
            logger.error(f"Error processing query directly: {e}")
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

            print("\n=== Agentic Hong Kong Weather Assistant ===")
            print("Type 'exit' or 'quit' to end the session")
            print("This assistant uses LLM to understand your queries and call appropriate tools")

            while True:
                query = input("\nWhat would you like to know about Hong Kong's weather? ")

                if query.lower() in ["exit", "quit"]:
                    logger.info("User requested to exit")
                    break

                print("\nProcessing your request...")
                response = await self.process_query_with_llm(query)
                print("\n" + response)

        finally:
            await self.close()

async def main():
    """Main function to run the client"""
    if len(sys.argv) < 2:
        logger.error("Server script path not provided")
        print("Usage: python agentic_weather_assistant.py <server_script_path>")
        sys.exit(1)

    server_script_path = sys.argv[1]
    logger.info(f"Starting client with server script: {server_script_path}")
    client = AgenticWeatherAssistant()
    await client.interactive_session(server_script_path)

if __name__ == "__main__":
    asyncio.run(main())
