import argparse
import os
import sys
from app.services.processor import AIChiefOfStaffProcessor
from app.llm.openai_llm import OpenAILLM
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
def main():
    parser = argparse.ArgumentParser(description="AI Chief of Staff CLI")

    parser.add_argument("--text", type=str, required=True, help="Input Text to process")

    args = parser.parse_args()

    llm = OpenAILLM(model = "gpt-4o-mini")  # Initialize your LLM here
    tools = None  # Initialize your tools here
    db = None  # Initialize your database here

    result = AIChiefOfStaffProcessor(llm, tools, db).process_input(args.text)

    print("\n===== FINAL OUTPUT =====\n")
    print(result.model_dump() if hasattr(result, "model_dump") else result)

    if __name__ == "__main__":
     main()