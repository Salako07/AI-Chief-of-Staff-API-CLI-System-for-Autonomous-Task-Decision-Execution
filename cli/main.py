import argparse
from app.services.processor import AIChiefOfStaffProcessor


def main():
    parser = argparse.ArgumentParser(description="AI Chief of Staff CLI")

    parser.add_argument("--text", type=str, required=True, help="Input Text to process")

    args = parser.parse_args()

    llm = None  # Initialize your LLM here
    tools = None  # Initialize your tools here
    db = None  # Initialize your database here

    result = AIChiefOfStaffProcessor(llm, tools, db).process_input(args.text)

    print("\n===== FINAL OUTPUT =====\n")
    print(result.model_dump() if hasattr(result, "model_dump") else result)

    if __name__ == "__main__":
     main()