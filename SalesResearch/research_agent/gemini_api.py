"""Gemini API integration for Deep Research and Business Model Canvas generation."""

import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig

load_dotenv()

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_AGENT = "deep-research-pro-preview-12-2025"
# Use Gemini 2.0 Flash for reasoning tasks
GEMINI_REASONING_MODEL = "gemini-2.0-flash-exp"

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


async def call_gemini_deep_research(prompt: str) -> str:
    """Call Gemini Deep Research API with streaming."""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not set in environment variables"

    try:
        print(f"⏳ Deep Research starting...\n")

        # Start streaming research
        stream = client.interactions.create(
            input=prompt,
            agent=GEMINI_AGENT,
            background=True,
            stream=True,
            agent_config={
                "type": "deep-research",
                "thinking_summaries": "auto"
            }
        )

        interaction_id = None

        # Stream thought summaries only
        for chunk in stream:
            if chunk.event_type == "interaction.start":
                interaction_id = chunk.interaction.id
                print(f"📋 Interaction ID: {interaction_id}\n")

            elif chunk.event_type == "content.delta":
                if hasattr(chunk.delta, 'type') and chunk.delta.type == "thought_summary":
                    print(f"\n💭 {chunk.delta.content.text}\n", flush=True)

            elif chunk.event_type == "interaction.complete":
                print(f"\n✅ Research completed!\n")
                break

        # Poll for final report
        if not interaction_id:
            return "Error: No interaction ID captured"

        print(f"📥 Fetching final research report...\n")

        max_retries = 100  # 100 retries x 20 seconds = ~33 minutes
        retry_count = 0

        while retry_count < max_retries:
            interaction = client.interactions.get(id=interaction_id)

            if interaction.status == "completed":
                if hasattr(interaction, 'outputs') and interaction.outputs and len(interaction.outputs) > 0:
                    final_report = interaction.outputs[-1].text
                    print(f"\n{'='*80}\nRESEARCH REPORT ({len(final_report)} characters):\n{'='*80}\n")
                    print(final_report)
                    print(f"\n{'='*80}\n")
                    return final_report
                else:
                    return f"No outputs in completed interaction {interaction_id}"

            elif interaction.status == "failed":
                error_msg = interaction.error if hasattr(interaction, 'error') else "Unknown error"
                return f"Research failed: {error_msg}"

            # Still processing
            print(f"⏳ Status: {interaction.status}, waiting...\n")
            await asyncio.sleep(20)
            retry_count += 1

        return f"Timeout after 33 minutes waiting for {interaction_id}"
    except Exception as e:
        return f"Error calling Gemini Deep Research: {str(e)}"


async def analyze_with_gemini(prompt: str) -> str:
    """Simple Gemini API call for analysis using SDK."""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not set"

    try:
        response = client.models.generate_content(
            model=GEMINI_REASONING_MODEL,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
