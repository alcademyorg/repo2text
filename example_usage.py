#!/usr/bin/env python3
"""
Example usage of repo2text library
"""

import os
from repo2text.core import RepoAnalyzer
from repo2text.utils import setup_logging


def main():
    """Example of using repo2text programmatically"""

    # Setup logging
    setup_logging(verbose=True)

    # Configuration
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITLAB_TOKEN")
    repo_url = "https://github.com/octocat/Hello-World"  # Example public repo

    # Initialize analyzer (token is optional for public repos)
    analyzer = RepoAnalyzer(
        token=token,  # Can be None for public repositories
        clone_dir="./example_clone",
        output_dir="./example_output",
        max_file_size_mb=5,
    )

    if token:
        print(f"Analyzing repository with authentication: {repo_url}")
    else:
        print(f"Analyzing public repository without authentication: {repo_url}")
        print("Note: Private repositories require a token")

    # Process repository
    result = analyzer.process_repository(repo_url, keep_clone=False)

    if result["success"]:
        print("\n✓ Analysis completed successfully!")
        print(f"Files processed: {result['files_processed']}")
        print(f"Binary files skipped: {result['binary_files_skipped']}")
        print(f"Large files skipped: {result['large_files_skipped']}")
        print(f"Encoding errors: {result['encoding_errors']}")
        print(f"Total characters: {result['total_characters']:,}")
        print(f"Total lines: {result['total_lines']:,}")
        print(f"Output file: {result['output_file']}")
    else:
        print(f"\n✗ Analysis failed: {result['error']}")


if __name__ == "__main__":
    main()
