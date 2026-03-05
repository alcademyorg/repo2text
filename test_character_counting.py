#!/usr/bin/env python3
"""
Test script to demonstrate character and line counting functionality
"""

import tempfile
import os
from pathlib import Path
from repo2text.core import RepoAnalyzer
from repo2text.utils import setup_logging


def create_test_files():
    """Create some test files to demonstrate character counting"""

    # Create a temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="repo2text_test_"))

    # Create test files with known content
    test_files = {
        "hello.txt": "Hello, World!\nThis is a test file.\n",
        "code.py": """#!/usr/bin/env python3
def hello():
    print("Hello from Python!")
    return True

if __name__ == "__main__":
    hello()
""",
        "data.json": """{
    "name": "test",
    "version": "1.0.0",
    "description": "A test JSON file"
}""",
        "README.md": """# Test Repository

This is a test repository for demonstrating character counting.

## Features
- Character counting
- Line counting
- File analysis
""",
    }

    for filename, content in test_files.items():
        file_path = temp_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return temp_dir, test_files


def test_character_counting():
    """Test the character counting functionality"""

    print("Testing Character and Line Counting Functionality")
    print("=" * 50)

    # Setup logging
    setup_logging(verbose=True)

    # Create test files
    test_dir, test_files = create_test_files()

    try:
        # Calculate expected counts
        expected_chars = sum(len(content) for content in test_files.values())
        expected_lines = sum(
            content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            for content in test_files.values()
        )

        print(f"Test directory: {test_dir}")
        print(f"Expected characters: {expected_chars:,}")
        print(f"Expected lines: {expected_lines:,}")
        print()

        # Create a mock analyzer (we'll test the counting logic directly)
        analyzer = RepoAnalyzer(
            token="dummy_token",  # Not used for local files
            clone_dir=str(test_dir),
            output_dir="./test_output",
            max_file_size_mb=10,
        )

        # Process the test files
        text_content = analyzer._convert_files_to_text(test_dir)

        print("Processing Results:")
        print("-" * 30)
        print(f"Files processed: {analyzer.stats['files_processed']}")
        print(f"Total characters: {analyzer.stats['total_characters']:,}")
        print(f"Total lines: {analyzer.stats['total_lines']:,}")
        print()

        # Verify the counts
        if analyzer.stats["total_characters"] == expected_chars:
            print("✓ Character count is correct!")
        else:
            print(
                f"✗ Character count mismatch: expected {expected_chars}, got {analyzer.stats['total_characters']}"
            )

        if analyzer.stats["total_lines"] == expected_lines:
            print("✓ Line count is correct!")
        else:
            print(
                f"✗ Line count mismatch: expected {expected_lines}, got {analyzer.stats['total_lines']}"
            )

        print()
        print("File Details:")
        print("-" * 30)
        for filename, content in test_files.items():
            chars = len(content)
            lines = content.count("\n") + (
                1 if content and not content.endswith("\n") else 0
            )
            print(f"{filename}: {chars} chars, {lines} lines")

        return (
            analyzer.stats["total_characters"] == expected_chars
            and analyzer.stats["total_lines"] == expected_lines
        )

    finally:
        # Cleanup
        import shutil

        shutil.rmtree(test_dir)


if __name__ == "__main__":
    success = test_character_counting()
    if success:
        print("\n✓ All character counting tests passed!")
    else:
        print("\n✗ Some tests failed!")
        exit(1)