#!/usr/bin/env python
"""Launch script for DevUI with the research agent."""

import logging
from agent_framework.devui import serve

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("     Sales Research Agent - DevUI")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Starting DevUI web interface...")
    logger.info("Available at: http://localhost:8080")
    logger.info("")
    logger.info("Required environment variables:")
    logger.info("  - PROJECT_ENDPOINT (Azure AI Foundry)")
    logger.info("  - MODEL_DEPLOYMENT_NAME")
    logger.info("")
    logger.info("Make sure 'az login' has been run for authentication")
    logger.info("")

    # Launch DevUI with directory discovery
    # It will automatically discover the research_agent folder
    serve(entities_dir=".", port=8080, auto_open=True)
