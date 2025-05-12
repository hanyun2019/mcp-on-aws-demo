# Hong Kong Weather Forecast Application
# By Haowen Huang
# 26 April, 2025

This application uses Amazon Nova Act and Model Context Protocol (MCP) to retrieve Hong Kong's daily weather forecast from the Hong Kong Observatory website.

## Features

- Retrieves current weather information for Hong Kong
- Fetches 9-day weather forecast
- Captures screenshots of weather forecast sections
- Allows querying weather for specific dates
- Stores and manages results

## Prerequisites

1. Operating System: macOS or Ubuntu (Nova Act requirements)
2. Python 3.10 or above
3. A valid Nova Act API key (obtain from https://nova.amazon.com/act)
4. Amazon Bedrock access:
   - Amazon Bedrock enabled in your AWS account
   - Claude 3.5 Sonnet V2 model enabled
   - AWS credentials and region properly configured

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd hk_weather_forecast
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your Nova Act API key as an environment variable:
   ```bash
   export NOVA_ACT_API_KEY="your_api_key"
   ```

4. Configure AWS credentials following the [AWS CLI Quickstart Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html)

## Usage

### Starting the Client and Server

```bash
python hk_weather_mcp_client.py hk_weather_mcp_server.py
```

This command will:
1. Start the MCP server that exposes Nova Act capabilities as tools
2. Launch the MCP client that connects to the server
3. Enable communication between Claude and the tools via the Model Context Protocol

### Example Queries

Once the application is running, you can ask questions like:

- "What's the current weather in Hong Kong?"
- "Show me the weather forecast for Hong Kong for the next week"
- "What will the weather be like in Hong Kong on 2025-05-01?"
- "Is it going to rain in Hong Kong tomorrow?"

## Architecture

This application consists of two main components:

1. **MCP Server (hk_weather_mcp_server.py)**:
   - Implements tools for retrieving weather data using Nova Act
   - Exposes these tools via the Model Context Protocol
   - Manages browser automation to navigate the Hong Kong Observatory website
   - Stores and processes results

2. **MCP Client (hk_weather_mcp_client.py)**:
   - Connects to the MCP server
   - Processes user queries using Amazon Bedrock (Claude 3.5 Sonnet)
   - Facilitates tool discovery and invocation via MCP
   - Handles tool responses and presents them to the user

## Understanding Model Context Protocol (MCP)

The Model Context Protocol (MCP) is a standardized protocol developed by Anthropic that enables LLMs like Claude to:

1. **Discover tools**: The LLM can query what tools are available and understand their capabilities
2. **Call tools**: The LLM can invoke tools with appropriate parameters
3. **Process responses**: The LLM can interpret and use the results returned by tools
4. **Maintain context**: The protocol supports multi-turn interactions with context preservation

In this application, MCP serves as the communication layer between Claude (via Amazon Bedrock) and the Nova Act browser automation tools.

## Troubleshooting

- If browser sessions fail to start, check your Nova Act API key
- For AWS credential issues, verify your AWS configuration
- If the Hong Kong Observatory website structure changes, the actions may need to be updated
- You might need to install Chrome with this command: `playwright install chrome`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
