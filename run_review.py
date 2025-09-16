import argparse
import difflib
import sys
from agents.reviewer_agent import DocumentationCheckTool

def main():
    """
    A simple script to check for documentation updates alongside code changes.
    This script directly uses the DocumentationCheckTool without the overhead
    of the full CrewAI agent framework, which is better suited for this
    deterministic task.
    """
    parser = argparse.ArgumentParser(
        description="Analyzes the diff between two files using the DocumentationCheckTool."
    )
    parser.add_argument("original_file", help="The path to the original file.")
    parser.add_argument("modified_file", help="The path to the modified file.")
    args = parser.parse_args()

    try:
        with open(args.original_file, 'r', encoding='utf-8') as f1:
            original_content = f1.readlines()
        with open(args.modified_file, 'r', encoding='utf-8') as f2:
            modified_content = f2.readlines()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate a unified diff
    diff_generator = difflib.unified_diff(
        original_content,
        modified_content,
        fromfile=args.original_file,
        tofile=args.modified_file,
        lineterm=''
    )
    diff_text = "".join(diff_generator)

    if not diff_text:
        print("PASS: No changes detected between the files.")
        sys.exit(0)

    # Instantiate the tool and run its logic directly
    checker_tool = DocumentationCheckTool()
    result = checker_tool._run(diff_content=diff_text)

    print("\n" + "="*30)
    print("   DOCUMENTATION CHECK RESULT")
    print("="*30)
    print(result)
    print("="*30 + "\n")

if __name__ == "__main__":
    main()
