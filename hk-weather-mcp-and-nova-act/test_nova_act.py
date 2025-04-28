#!/usr/bin/env python
# test_nova_act.py

import os
from nova_act import NovaAct

# Check for API key
NOVA_ACT_API_KEY = os.getenv("NOVA_ACT_API_KEY")
if not NOVA_ACT_API_KEY:
    print("Error: NOVA_ACT_API_KEY environment variable not set")
    exit(1)

print("Testing Nova Act with Hong Kong Observatory website...")

try:
    # Create and start NovaAct instance
    with NovaAct(
        starting_page="https://www.hko.gov.hk/en/index.html",
        headless=False,
    ) as nova_act:
        # Find and extract current weather information
        print("Retrieving current weather information...")
        result = nova_act.act("Find and read the current weather information for Hong Kong")

        print("\nCurrent Weather in Hong Kong:")
        print(result.response)

        print("\nTest completed successfully!")

except Exception as e:
    print(f"Error during test: {str(e)}")
