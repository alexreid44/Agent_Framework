# pip install agent-framework-azure-ai --pre
# Use `az login` to authenticate with Azure CLI
"""Sales Research Agent for DevUI - Main agent definition."""

import os
from pathlib import Path
from typing import Annotated
from agent_framework import ai_function, ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

# Import helper modules
from .gemini_api import call_gemini_deep_research, analyze_with_gemini
from .file_utils import generate_filename, save_research_pdf, save_business_model_canvas_docx

# Load environment variables
load_dotenv()



@ai_function(
    name="gemini_research_tool",
    description="Returns research on a given company using Gemini Deep Research.",
    approval_mode="always_require"
)
async def gemini_deep_research(
    company_name: Annotated[str, "The name of the company to research."],
    company_url: Annotated[str, "The URL of the company's website."],
) -> str:
    """Perform deep research on a company using Gemini Deep Research API, then generate Business Model Canvas."""

    # Load the research prompt template
    prompts_dir = Path(__file__).parent.parent / "Prompts"
    prompt_file = prompts_dir / "DeepResearch.txt"

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        return f"Error: Could not find prompt file at {prompt_file}"

    # Replace placeholders with actual company information
    prompt = prompt_template.replace("[Company Name]", company_name)
    prompt = prompt.replace("[Company URL]", company_url)

    print(f"\n🔍 Starting deep research on {company_name}...")

    # Call Gemini Deep Research API
    research_result = await call_gemini_deep_research(prompt)

    print(f"✅ Deep research completed!\n")
    print(research_result)

    # Prepare output directory
    output_dir = Path(__file__).parent.parent / "deep_research"
    output_dir.mkdir(exist_ok=True)

    # Generate filenames
    base_filename, timestamp = generate_filename(company_name)
    bmc_filename, _ = generate_filename(company_name, suffix="_BusinessModelCanvas")

    try:
        print(f"💾 Saving research report as PDF...")

        # Save research as PDF
        pdf_file = save_research_pdf(
            output_dir, base_filename, company_name, company_url, research_result
        )

        print(f"✅ Report saved: {pdf_file.name}\n")
        print(f"🧠 Generating Business Model Canvas from research...")

        # Generate Business Model Canvas from the research text
        bmc_prompt = f"""Analyze this research on {company_name} and create a Business Model Canvas.

{research_result}

Create sections: Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Resources, Key Activities, Key Partnerships, Cost Structure.

**IMPORTANT: Format your response as clean HTML using semantic tags like <h2>, <h3>, <p>, <ul>, <li>, <strong>, etc. Do NOT use markdown. Do NOT include <!DOCTYPE> or <html> wrapper tags - just the content HTML.**"""

        bmc_result = await analyze_with_gemini(bmc_prompt)

        print(f"✅ Business Model Canvas generated!\n")
        print(f"💾 Saving Business Model Canvas as Word document...")

        # Save Business Model Canvas
        docx_file = save_business_model_canvas_docx(
            output_dir, bmc_filename, company_name, company_url, bmc_result
        )

        print(f"✅ Document saved: {docx_file.name}\n")
        print(f"🎉 All done!\n")

        return (
            f"{research_result}\n\n"
            f"---\n\n"
            f"✅ Research: {pdf_file.name}\n"
            f"✅ Business Model Canvas: {docx_file.name}"
        )
    except Exception as e:
        return (
            f"{research_result}\n\n"
            f"---\n\n"
            f"⚠️ Error saving files: {str(e)}"
        )


# Create and export the agent for DevUI discovery
agent = ChatAgent(
    name="ResearchAssistant",
    description="A research assistant that performs deep research on companies",
    instructions=(
        "You are a research assistant that provides detailed information about companies. "
        "Your goal is to determine the company name and company URL, then use the "
        "gemini_research_tool to gather information. Return exactly what the tool returns."
    ),
    chat_client=AzureAIAgentClient(
        credential=AzureCliCredential(),
        project_endpoint=os.environ["PROJECT_ENDPOINT"],
        model_deployment_name=os.environ["MODEL_DEPLOYMENT_NAME"],
        agent_name="research-assistant",
        agent_description="A research assistant that performs deep research on companies using Gemini Deep Research",
    ),
    tools=[gemini_deep_research],
    greeting="Hello! I am your research assistant. Which company would you like to research today?",
)
