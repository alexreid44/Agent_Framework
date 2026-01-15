"""Gemini API integration for Deep Research and Business Model Canvas generation."""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_AGENT = "deep-research-pro-preview-12-2025"
GEMINI_REASONING_MODEL = "gemini-2.5-pro-exp-03-25"


async def call_gemini_deep_research(prompt: str) -> str:
    """Call Gemini Deep Research API and poll for results."""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not set in environment variables"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        # Step 1: Start the research task
        payload = {
            "input": prompt,
            "agent": GEMINI_AGENT,
            "background": True
        }

        try:
            async with session.post(
                f"{GEMINI_API_BASE}/interactions",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return f"Error starting research: {response.status} - {error_text}"

                result = await response.json()
                interaction_id = result.get("id")

                if not interaction_id:
                    return f"Error: No interaction ID returned from API. Response: {result}"

        except Exception as e:
            return f"Error calling Gemini API: {str(e)}"

        # Step 2: Poll for results
        max_attempts = 60  # Poll for up to 5 minutes (60 * 5 seconds)
        poll_interval = 5  # seconds

        for attempt in range(max_attempts):
            await asyncio.sleep(poll_interval)

            try:
                async with session.get(
                    f"{GEMINI_API_BASE}/interactions/{interaction_id}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return f"Error polling results: {response.status} - {error_text}"

                    result = await response.json()
                    state = result.get("state", "")

                    # Check if completed
                    if state == "COMPLETED":
                        output = result.get("output", "")
                        if output:
                            return output
                        else:
                            return f"Research completed but no output found. Full response: {result}"

                    elif state in ["FAILED", "CANCELLED"]:
                        error = result.get("error", "Unknown error")
                        return f"Research {state.lower()}: {error}"

                    # Still processing, continue polling

            except Exception as e:
                return f"Error polling Gemini API: {str(e)}"

        return f"Research timed out after {max_attempts * poll_interval} seconds. The research may still be processing."


async def generate_business_model_canvas(company_name: str, research_report: str) -> str:
    """Generate Business Model Canvas using Gemini 2.5 Pro reasoning model."""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not set in environment variables"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    # Business Model Canvas analysis prompt
    bmc_prompt = f"""Analyze the research report on {company_name}. Use your advanced reasoning skills to complete each section of the Business Model Canvas.

Here is the research report:

{research_report}

Please provide a comprehensive Business Model Canvas with the following sections:

1. **Customer Segments**: Who are the key customer groups?
2. **Value Propositions**: What unique value does the company offer to each segment?
3. **Channels**: Through what channels does the company reach and deliver value?
4. **Customer Relationships**: What types of relationships does the company establish with customers?
5. **Revenue Streams**: How does the company generate revenue from each customer segment?
6. **Key Resources**: What key resources are required for the business model to work?
7. **Key Activities**: What key activities are necessary to deliver the value proposition?
8. **Key Partnerships**: Who are the key partners and suppliers?
9. **Cost Structure**: What are the most important costs inherent in the business model?

Format your response as a clear, structured markdown document."""

    async with aiohttp.ClientSession() as session:
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": bmc_prompt}
                    ]
                }
            ]
        }

        try:
            async with session.post(
                f"{GEMINI_API_BASE}/models/{GEMINI_REASONING_MODEL}:generateContent",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return f"Error calling Gemini 2.5 Pro: {response.status} - {error_text}"

                result = await response.json()

                # Extract the generated text from the response
                candidates = result.get("candidates", [])
                if candidates and len(candidates) > 0:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts and len(parts) > 0:
                        return parts[0].get("text", "No text generated")

                return f"Error: Unexpected response format. Response: {result}"

        except Exception as e:
            return f"Error calling Gemini 2.5 Pro API: {str(e)}"
