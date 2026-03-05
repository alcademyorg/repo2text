#!/usr/bin/env python3
"""
Main CLI interface for repo2text
"""

import click
import os
import sys
from pathlib import Path

from .core import RepoAnalyzer
from .utils import validate_repo_url, setup_logging


@click.command()
@click.option(
    "--token",
    "-t",
    help="GitHub or GitLab personal access token (optional, required for private repositories)",
)
@click.option(
    "--repo-url", "-r", required=True, help="GitHub or GitLab repository URL (HTTPS)"
)
@click.option(
    "--output-dir",
    "-o",
    default="./output",
    help="Output directory for text files (default: ./output)",
)
@click.option(
    "--clone-dir",
    "-c",
    default="./temp_clone",
    help="Temporary directory for cloning (default: ./temp_clone)",
)
@click.option(
    "--keep-clone",
    is_flag=True,
    default=False,
    help="Keep the cloned repository after processing",
)
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Enable verbose logging"
)
@click.option(
    "--max-file-size",
    default=10,
    help="Maximum file size in MB to process (default: 10MB)",
)
@click.option(
    "--branch",
    "-b",
    default=None,
    help="Specific branch to clone (default: repository's default branch)",
)
def main(
    token, repo_url, output_dir, clone_dir, keep_clone, verbose, max_file_size, branch
):
    """
    Clone a GitHub/GitLab repository and convert all non-binary files to text format.

    This tool will:
    1. Clone the specified repository (with or without authentication)
    2. Analyze all files to identify non-binary content
    3. Convert and organize files into a text-based structure
    4. Generate a comprehensive text output

    Examples:
        # Public repository (no token required)
        repo2text -r https://github.com/user/public-repo

        # Private repository (token required)
        repo2text -t your_github_token -r https://github.com/user/private-repo
        repo2text -t your_gitlab_token -r https://gitlab.com/user/repo
        repo2text -t username:your_gitlab_token -r https://gitlab.com/user/repo

        # Specific branch
        repo2text -r https://github.com/user/public-repo -b develop
        repo2text -r https://github.com/user/public-repo --branch feature/new-feature
    """

    # Setup logging
    setup_logging(verbose)

    try:
        # Validate repository URL
        if not validate_repo_url(repo_url):
            click.echo(
                click.style("Error: Invalid repository URL format", fg="red"), err=True
            )
            sys.exit(1)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Initialize the analyzer
        analyzer = RepoAnalyzer(
            token=token,
            clone_dir=clone_dir,
            output_dir=output_dir,
            max_file_size_mb=max_file_size,
        )

        if token:
            branch_info = f" (branch: {branch})" if branch else ""
            click.echo(
                click.style(
                    f"Starting analysis of: {repo_url}{branch_info} (with authentication)",
                    fg="green",
                )
            )
        else:
            branch_info = f" (branch: {branch})" if branch else ""
            click.echo(
                click.style(
                    f"Starting analysis of: {repo_url}{branch_info} (no authentication - public repo only)",
                    fg="green",
                )
            )

        # Process the repository
        result = analyzer.process_repository(repo_url, keep_clone, branch)

        if result["success"]:
            click.echo(click.style("✓ Repository processed successfully!", fg="green"))
            click.echo(f"Files processed: {result['files_processed']}")
            click.echo(f"Binary files skipped: {result['binary_files_skipped']}")
            click.echo(f"Large files skipped: {result['large_files_skipped']}")
            click.echo(f"Encoding errors: {result['encoding_errors']}")
            click.echo(f"Total characters: {result['total_characters']:,}")
            click.echo(f"Total lines: {result['total_lines']:,}")
            click.echo(f"Output directory: {output_dir}")
            click.echo(f"Main output file: {result['output_file']}")
        else:
            click.echo(click.style(f"✗ Error: {result['error']}", fg="red"), err=True)
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo(
            click.style("\n✗ Operation cancelled by user", fg="yellow"), err=True
        )
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Unexpected error: {str(e)}", fg="red"), err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()