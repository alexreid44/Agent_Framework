# pip install agent-framework-azure-ai --pre
# Use `az login` to authenticate with Azure CLI
import os
import asyncio
import json
from dotenv import load_dotenv
from typing import Annotated
from agent_framework import ai_function, ChatMessage, Role, TextContent
from agent_framework.azure import AzureAIClient
from azure.identity.aio import DefaultAzureCredential

# Load environment variables from .env file
load_dotenv()

# Define a custom AI function for Gemini Deep Research
@ai_function(name="gemini_research_tool", description="Returns research on a given company using Gemini Deep Research.", approval_mode="always_require")
def gemini_deep_research(
    company_name: Annotated[str, "The name of the company to research."],
    company_url: Annotated[str, "The URL of the company's website."],
) -> str:
    return "true"


async def main():
    async with (
        DefaultAzureCredential() as credential,
        AzureAIClient(
            project_endpoint=os.environ["PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ).create_agent(
            name="research-assistant",
            instructions="You are a research assistant that provides detailed information about companies. Your goal is to determine the company name and company URL, then use the gemini_research_tool to gather information.",
            tools=[gemini_deep_research]
        ) as agent,
    ):
        # Prompt user for company to research
        company_input = input("What company would you like to research today? ").strip()
        if not company_input:
            print("No company entered. Exiting...")
            return

        user_query = f"Tell me about {company_input}"
        result = await agent.run(user_query)

        # Continue iterating until function is approved or user quits
        while result.user_input_requests:
            for user_input_needed in result.user_input_requests:
                # Parse arguments to extract company details
                try:
                    args = json.loads(user_input_needed.function_call.arguments)
                    company_name = args.get("company_name", "Unknown")
                    company_url = args.get("company_url", "Unknown")
                except:
                    company_name = "Unknown"
                    company_url = "Unknown"

                # Display formatted approval request
                print("\n" + "="*60)
                print("           Deep Research Requested")
                print("="*60)
                print(f"Company:     {company_name}")
                print(f"Company URL: {company_url}")
                print("="*60)

                # Get natural language response from user
                user_response = input("\nWould you like to perform deep research on this company?\n(If not, explain what you would like changed, or type 'quit' to exit)\n\nYour response: ").strip()

                if not user_response or user_response.lower() == 'quit':
                    print("\nExiting research session...")
                    return

                # Send user's natural language response to the agent
                response_message = ChatMessage(
                    role=Role.USER,
                    contents=[TextContent(text=user_response)]
                )

                result = await agent.run(response_message)

                # If there are no more approval requests, the function was executed
                if not result.user_input_requests:
                    if result.text:
                        print(f"\n{'='*60}")
                        print("Agent Response:")
                        print('='*60)
                        print(result.text)
                        print('='*60)
                    else:
                        print("\nResearch completed successfully!")
                    return
                # Otherwise, loop continues to show the updated approval request

        # No approval needed, print the result directly
        if result.text:
            print(f"\nAgent: {result.text}")

if __name__ == "__main__":
    asyncio.run(main())