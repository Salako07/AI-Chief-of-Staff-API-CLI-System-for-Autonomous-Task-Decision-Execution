from app.services.processor import AIChiefOfStaffProcessor
from app.api.schema import ProcessRequest, ProcessResponse
import uuid
import logging
import os

logger = logging.getLogger(__name__)

processor = None

def init_process(llm, tools, db, slack_webhook_url: str = None):
    """
    Initialize the processor with optional Slack integration.

    Args:
        llm: Language model instance
        tools: Tools for execution
        db: Database connection
        slack_webhook_url: Optional Slack webhook URL for notifications
    """
    global processor

    # Get Slack webhook from parameter or environment variable
    webhook_url = slack_webhook_url or os.getenv("SLACK_WEBHOOK_URL")

    processor = AIChiefOfStaffProcessor(llm, tools, db, slack_webhook_url=webhook_url)

    if webhook_url:
        logger.info("Processor initialized successfully with Slack integration")
    else:
        logger.info("Processor initialized successfully (Slack notifications disabled)")


def process_handler(request: ProcessRequest) -> ProcessResponse:
    global processor

    # Fixed: Add null check for uninitialized processor
    if processor is None:
        logger.error("Processor not initialized. Call init_process() first.")
        raise RuntimeError("Processor not initialized. Please initialize the system before processing requests.")

    logger.info(f"Processing input from source: {request.source}")

    try:
        result = processor.process_input(request.text)

        return ProcessResponse(
            run_id=result.metadata.run_id if result.metadata.run_id else str(uuid.uuid4()),
            tasks=result.tasks,
            decisions=result.decisions,
            risks=result.risks,
            summary=result.summary
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise