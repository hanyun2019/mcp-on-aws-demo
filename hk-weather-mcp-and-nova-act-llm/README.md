# Agentic Weather Assistant with MCP and Nova Act
# by Haowen Huang 
# 12 May, 2025

This project demonstrates how to build an AI agent that uses the Model Context Protocol (MCP) to bridge the gap between large language models and real-world data sources. The agent leverages Amazon Bedrock and Nova Act to create a context-aware application that can retrieve and interpret weather information from the Hong Kong Observatory website.

## Overview

The Agentic Weather Assistant showcases:

1. How MCP creates a bridge between AI models and real-world data sources
2. Using Amazon Bedrock to power natural language understanding
3. Leveraging Nova Act for web interaction and data extraction
4. Building a context-aware application that can respond to user queries intelligently

## Components

- **MCP Server (`hk_weather_mcp_server.py`)**: Provides tools for retrieving weather data using Nova Act
- **MCP Client (`hk_weather_mcp_client.py`)**: Basic client that connects to the MCP server and calls tools based on keywords
- **Agentic Assistant (`agentic_weather_assistant.py`)**: Enhanced client that uses Amazon Bedrock to understand user queries and intelligently call the appropriate tools

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  User Query     │────▶│  Bedrock LLM    │────▶│  Tool Selection │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Response       │◀────│  Result         │◀────│  MCP Tool Call  │
│  Generation     │     │  Processing     │     │                 │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  Nova Act       │
                                                │  Web Scraping   │
                                                │                 │
                                                └─────────────────┘
```

## Key Features

- **Natural Language Understanding**: Uses Amazon Bedrock to understand user queries and determine the appropriate tool to call
- **Tool Selection**: Intelligently selects between current weather, forecast, and warnings tools
- **Fallback Mechanism**: If the LLM-based approach fails, falls back to keyword-based tool selection
- **Data Interpretation**: Processes the raw data from the tools to provide meaningful insights
- **Screenshot Capture**: Takes screenshots of the weather information for visual reference

## Requirements

- Python 3.8+
- AWS account with access to Amazon Bedrock
- Nova Act API key
- Required Python packages (see `requirements.txt`)

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up your environment variables:
   ```
   export NOVA_ACT_API_KEY=your_api_key
   export AWS_PROFILE=your_aws_profile  # Optional
   ```

3. Run the MCP server:
   ```
   python hk_weather_mcp_server.py
   ```

4. In a separate terminal, run the agentic assistant:
   ```
   python agentic_weather_assistant.py hk_weather_mcp_server.py
   ```

## Usage

Once the assistant is running, you can ask questions about Hong Kong's weather in natural language:

- "What's the weather like in Hong Kong today?"
- "Will it rain tomorrow in Hong Kong?"
- "Give me the forecast for the next week"
- "Are there any weather warnings in Hong Kong right now?"
- "What's the temperature and humidity in Hong Kong?"
- "Should I bring an umbrella if I'm going out this afternoon?"

The assistant will use the LLM to understand your query, select the appropriate tool, and provide a meaningful response based on the real-time data from the Hong Kong Observatory website.

## How It Works

1. The user enters a natural language query about Hong Kong's weather
2. The query is sent to Amazon Bedrock, which determines the appropriate tool to call
3. The selected tool is called via MCP, which triggers Nova Act to retrieve data from the Hong Kong Observatory website
4. The raw data is processed and returned to Bedrock
5. Bedrock generates a human-friendly response based on the data
6. The response is presented to the user

## Benefits of Using MCP

- **Separation of Concerns**: The MCP server handles the web scraping logic, while the client focuses on user interaction
- **Reusability**: The same MCP tools can be used by different clients
- **Extensibility**: New tools can be added to the MCP server without changing the client
- **Flexibility**: The client can switch between LLM-based and keyword-based approaches as needed

## Future Enhancements

- Add support for more weather data sources
- Implement caching to reduce API calls
- Add location-based weather queries for other cities
- Enhance the response with weather trends and patterns
- Integrate with other data sources for more comprehensive information
