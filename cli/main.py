import argparse
import os
import sys
import logging
import json
from datetime import datetime
from app.services.processor import AIChiefOfStaffProcessor
from app.llm.openai_llm import OpenAILLM
from crewai import LLM

# Configure logging
def setup_logging(verbose=False):
    """Setup structured logging for the CLI"""
    log_level = logging.DEBUG if verbose else logging.INFO

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # File handler with timestamp
    log_file = os.path.join(log_dir, f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def main():
    parser = argparse.ArgumentParser(description="AI Chief of Staff CLI - Extract tasks, decisions, and risks from text")

    parser.add_argument("--text", type=str, required=True, help="Input text to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output", "-o", type=str, help="Output file path for JSON results")
    parser.add_argument("--slack-webhook", type=str, help="Slack webhook URL for notifications (overrides SLACK_WEBHOOK_URL env var)")

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.verbose)
    logger.info("AI Chief of Staff CLI started")
    logger.info(f"Input length: {len(args.text)} characters")

    try:
        # Initialize LLM
        Llm = LLM(model="gpt-4o-mini")
        tools = None
        db = None

        # Get Slack webhook URL from args or environment
        slack_webhook_url = args.slack_webhook or os.getenv("SLACK_WEBHOOK_URL")

        logger.info("Initializing processor...")
        processor = AIChiefOfStaffProcessor(Llm, tools, db, slack_webhook_url=slack_webhook_url)

        logger.info("Processing input...")
        result = processor.process_input(args.text)

        # Convert result to dict
        result_dict = result.model_dump() if hasattr(result, "model_dump") else result

        # Print results
        print("\n" + "="*60)
        print("AI CHIEF OF STAFF - PROCESSING RESULTS")
        print("="*60)
        print(f"\nRun ID: {result.metadata.run_id}")
        print(f"Processed at: {result.metadata.processed_at}")
        print(f"\nTASKS ({len(result.tasks)}):")
        print("-" * 60)
        for i, task in enumerate(result.tasks, 1):
            print(f"{i}. {task.title}")
            if task.owner:
                print(f"   Owner: {task.owner}")
            if task.deadline:
                print(f"   Deadline: {task.deadline}")
            print(f"   Priority: {task.priority}")
            print()

        print(f"DECISIONS ({len(result.decisions)}):")
        print("-" * 60)
        for i, decision in enumerate(result.decisions, 1):
            print(f"{i}. {decision.decision}")
            if decision.made_by:
                print(f"   Made by: {decision.made_by}")
            print()

        print(f"RISKS ({len(result.risks)}):")
        print("-" * 60)
        for i, risk in enumerate(result.risks, 1):
            print(f"{i}. {risk.risk}")
            print(f"   Severity: {risk.severity}")
            if risk.mitigation:
                print(f"   Mitigation: {risk.mitigation}")
            print()

        print("SUMMARY:")
        print("-" * 60)
        print(result.summary)
        print("\n" + "="*60)

        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result_dict, f, indent=2, default=str)
            logger.info(f"Results saved to: {args.output}")
            print(f"\nResults saved to: {args.output}")

        logger.info("Processing completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())