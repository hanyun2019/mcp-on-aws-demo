#!/usr/bin/env python
# test_forecast.py

import os
from nova_act import NovaAct

# Check for API key
NOVA_ACT_API_KEY = os.getenv("NOVA_ACT_API_KEY")
if not NOVA_ACT_API_KEY:
    print("Error: NOVA_ACT_API_KEY environment variable not set")
    exit(1)

print("Testing Nova Act with Hong Kong Observatory 9-day forecast...")

try:
    # Create and start NovaAct instance
    with NovaAct(
        # Start directly on the 9-day forecast page
        starting_page="https://www.hko.gov.hk/en/wxinfo/currwx/fnd.htm",
        headless=False,
    ) as nova_act:
        # Find and extract forecast information
        print("Retrieving 9-day forecast information...")
        result = nova_act.act("Read and extract the complete 9-day weather forecast information visible on this page")

        print("\n9-Day Weather Forecast for Hong Kong:")
        print(result.response)

        print("\nTest completed successfully!")

except Exception as e:
    print(f"Error during test: {str(e)}")