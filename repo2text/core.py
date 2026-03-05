"""
Core functionality for repository analysis and text conversion
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import tempfile

import git
from git import Repo
import magic
import chardet

from .utils import is_binary_file, get_file_encoding, sanitize_filename


logger = logging.getLogger(__name__)


class RepoAnalyzer:
    """Main class for analyzing repositories and converting files to text"""

    def __init__(
        self,
        token: Optional[str] = None,
        clone_dir: str = "./temp_clone",
        output_dir: str = "./output",
        max_file_size_mb: int = 10,
    ):
        self.token = token
        self.clone_dir = Path(clone_dir)
        self.output_dir = Path(output_dir)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

        # Statistics
        self.stats = {
            "files_processed": 0,
            "binary_files_skipped": 0,
            "large_files_skipped": 0,
            "encoding_errors": 0,
            "total_characters": 0,
            "total_lines": 0,
        }

    def process_repository(
        self, repo_url: str, keep_clone: bool = False, branch: Optional[str] = None
    ) -> Dict:
        """
        Main method to process a repository

        Args:
            repo_url: GitHub/GitLab repository URL
            keep_clone: Whether to keep the cloned repository
            branch: Specific branch to clone (optional)

        Returns:
            Dictionary with processing results
        """
        try:
            # Clone the repository
            branch_info = f" (branch: {branch})" if branch else ""
            logger.info(f"Cloning repository: {repo_url}{branch_info}")
            repo_path = self._clone_repository(repo_url, branch)

            # Analyze and convert files
            logger.info("Analyzing repository structure...")
            file_tree = self._analyze_repository_structure(repo_path)

            logger.info("Converting files to text...")
            text_content = self._convert_files_to_text(repo_path)

            # Generate output
            output_file = self._generate_output(
                repo_url, file_tree, text_content, branch
            )

            # Cleanup
            if not keep_clone and repo_path.exists():
                logger.info("Cleaning up cloned repository...")
                shutil.rmtree(repo_path)

            return {
                "success": True,
                "files_processed": self.stats["files_processed"],
                "binary_files_skipped": self.stats["binary_files_skipped"],
                "large_files_skipped": self.stats["large_files_skipped"],
                "encoding_errors": self.stats["encoding_errors"],
                "total_characters": self.stats["total_characters"],
                "total_lines": self.stats["total_lines"],
                "output_file": str(output_file),
            }

        except Exception as e:
            logger.error(f"Error processing repository: {str(e)}")
            return {"success": False, "error": str(e)}

    def _clone_repository(self, repo_url: str, branch: Optional[str] = None) -> Path:
        """Clone the repository using the provided token if available, otherwise clone without authentication"""

        # Clean up existing clone directory
        if self.clone_dir.exists():
            shutil.rmtree(self.clone_dir)

        # If no token is provided, try to clone without authentication (for public repos)
        if not self.token:
            logger.info(
                "No token provided, attempting to clone public repository without authentication"
            )
            try:
                if branch:
                    repo = Repo.clone_from(repo_url, self.clone_dir, branch=branch)
                    logger.info(
                        f"Successfully cloned repository (branch: {branch}) to {self.clone_dir}"
                    )
                else:
                    repo = Repo.clone_from(repo_url, self.clone_dir)
                    logger.info(f"Successfully cloned repository to {self.clone_dir}")
                return self.clone_dir
            except git.exc.GitCommandError as e:
                if (
                    "authentication" in str(e).lower()
                    or "permission denied" in str(e).lower()
                ):
                    raise Exception(
                        "Authentication required for this repository. Please provide a token using --token/-t option."
                    )
                elif "not found" in str(e).lower():
                    if branch:
                        raise Exception(
                            f"Repository not found or branch '{branch}' does not exist. Please check the URL and branch name."
                        )
                    else:
                        raise Exception("Repository not found. Please check the URL.")
                else:
                    raise Exception(f"Git clone failed: {str(e)}")

        # Parse URL and inject token for authenticated cloning
        parsed_url = urlparse(repo_url)

        if "github.com" in parsed_url.netloc:
            # GitHub format: https://token@github.com/user/repo.git
            auth_url = f"https://{self.token}@{parsed_url.netloc}{parsed_url.path}"
        elif "gitlab.com" in parsed_url.netloc or "gitlab" in parsed_url.netloc:
            # GitLab format: https://username:token@gitlab.com/user/repo.git
            # If token contains ':', treat it as username:token format
            # Otherwise, use 'gitlab-ci-token' as default username
            if ":" in self.token:
                auth_url = f"https://{self.token}@{parsed_url.netloc}{parsed_url.path}"
            else:
                auth_url = f"https://gitlab-ci-token:{self.token}@{parsed_url.netloc}{parsed_url.path}"
        else:
            # Generic format, assume GitHub-like
            auth_url = f"https://{self.token}@{parsed_url.netloc}{parsed_url.path}"

        # Ensure .git extension
        if not auth_url.endswith(".git"):
            auth_url += ".git"

        # Clone the repository with authentication
        try:
            if branch:
                repo = Repo.clone_from(auth_url, self.clone_dir, branch=branch)
                logger.info(
                    f"Successfully cloned repository (branch: {branch}) to {self.clone_dir}"
                )
            else:
                repo = Repo.clone_from(auth_url, self.clone_dir)
                logger.info(f"Successfully cloned repository to {self.clone_dir}")
            return self.clone_dir
        except git.exc.GitCommandError as e:
            if "authentication failed" in str(e).lower():
                raise Exception(
                    "Authentication failed. Please check your token and repository access."
                )
            elif "not found" in str(e).lower():
                if branch:
                    raise Exception(
                        f"Repository not found or branch '{branch}' does not exist. Please check the URL and branch name."
                    )
                else:
                    raise Exception("Repository not found. Please check the URL.")
            else:
                raise Exception(f"Git clone failed: {str(e)}")

    def _analyze_repository_structure(self, repo_path: Path) -> Dict:
        """Analyze the repository structure and create a file tree"""

        def build_tree(path: Path, prefix: str = "") -> List[str]:
            """Recursively build a tree structure"""
            items = []
            try:
                # Get all items and sort them (directories first, then files)
                all_items = list(path.iterdir())
                dirs = [
                    item
                    for item in all_items
                    if item.is_dir() and not item.name.startswith(".git")
                ]
                files = [item for item in all_items if item.is_file()]

                dirs.sort(key=lambda x: x.name.lower())
                files.sort(key=lambda x: x.name.lower())

                # Process directories
                for i, dir_path in enumerate(dirs):
                    is_last_dir = (i == len(dirs) - 1) and len(files) == 0
                    connector = "└── " if is_last_dir else "├── "
                    items.append(f"{prefix}{connector}{dir_path.name}/")

                    extension = "    " if is_last_dir else "│   "
                    items.extend(build_tree(dir_path, prefix + extension))

                # Process files
                for i, file_path in enumerate(files):
                    is_last = i == len(files) - 1
                    connector = "└── " if is_last else "├── "

                    # Add file size info
                    try:
                        size = file_path.stat().st_size
                        size_str = self._format_file_size(size)
                        items.append(
                            f"{prefix}{connector}{file_path.name} ({size_str})"
                        )
                    except:
                        items.append(f"{prefix}{connector}{file_path.name}")

            except PermissionError:
                items.append(f"{prefix}[Permission Denied]")

            return items

        # Get the actual repository name from the remote origin URL instead of using clone directory name
        try:
            repo = Repo(repo_path)
            remote_url = repo.remotes.origin.url
            # Extract repository name from URL (e.g., from https://github.com/user/repo.git get 'repo')
            repo_name = Path(urlparse(remote_url).path).stem
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]  # Remove .git suffix if present
        except:
            # Fallback to directory name if we can't get the remote URL
            repo_name = repo_path.name

        tree_lines = [f"{repo_name}/"]
        tree_lines.extend(build_tree(repo_path))

        return {
            "tree": "\n".join(tree_lines),
            "total_files": len(list(repo_path.rglob("*"))),
            "total_dirs": len([p for p in repo_path.rglob("*") if p.is_dir()]),
        }

    def _convert_files_to_text(self, repo_path: Path) -> Dict[str, str]:
        """Convert all non-binary files to text content"""

        text_files = {}

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip .git directory
            if ".git" in file_path.parts:
                continue

            # Get relative path for organization
            rel_path = file_path.relative_to(repo_path)

            try:
                # Check file size
                file_size = file_path.stat().st_size
                if file_size > self.max_file_size_bytes:
                    logger.warning(
                        f"Skipping large file: {rel_path} ({self._format_file_size(file_size)})"
                    )
                    self.stats["large_files_skipped"] += 1
                    continue

                # Check if file is binary
                if is_binary_file(file_path):
                    logger.debug(f"Skipping binary file: {rel_path}")
                    self.stats["binary_files_skipped"] += 1
                    continue

                # Read and decode file content
                content = self._read_file_content(file_path)
                if content is not None:
                    text_files[str(rel_path)] = content
                    self.stats["files_processed"] += 1

                    # Count characters and lines
                    self.stats["total_characters"] += len(content)
                    self.stats["total_lines"] += content.count("\n") + (
                        1 if content and not content.endswith("\n") else 0
                    )

                    logger.debug(f"Processed: {rel_path}")
                else:
                    self.stats["encoding_errors"] += 1

            except Exception as e:
                logger.warning(f"Error processing {rel_path}: {str(e)}")
                self.stats["encoding_errors"] += 1

        return text_files

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with proper encoding detection"""

        try:
            # First, try to detect encoding
            with open(file_path, "rb") as f:
                raw_data = f.read()

            # Detect encoding
            encoding_info = chardet.detect(raw_data)
            encoding = encoding_info.get("encoding", "utf-8")
            confidence = encoding_info.get("confidence", 0)

            # If confidence is too low, try common encodings
            if confidence < 0.7:
                for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                    try:
                        content = raw_data.decode(enc)
                        return content
                    except UnicodeDecodeError:
                        continue

                # If all fail, use utf-8 with error handling
                return raw_data.decode("utf-8", errors="replace")
            else:
                return raw_data.decode(encoding)

        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {str(e)}")
            return None

    def _generate_output(
        self,
        repo_url: str,
        file_tree: Dict,
        text_content: Dict[str, str],
        branch: Optional[str] = None,
    ) -> Path:
        """Generate the final text output file"""

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        repo_name = Path(urlparse(repo_url).path).stem
        branch_suffix = f"_{sanitize_filename(branch)}" if branch else ""
        output_file = (
            self.output_dir
            / f"{sanitize_filename(repo_name)}{branch_suffix}_analysis.txt"
        )

        with open(output_file, "w", encoding="utf-8") as f:
            # Header
            f.write("=" * 80 + "\n")
            branch_info = f" (branch: {branch})" if branch else ""
            f.write(f"REPOSITORY ANALYSIS: {repo_url}{branch_info}\n")
            f.write("=" * 80 + "\n\n")

            # Statistics
            f.write("PROCESSING STATISTICS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Files processed: {self.stats['files_processed']}\n")
            f.write(f"Binary files skipped: {self.stats['binary_files_skipped']}\n")
            f.write(f"Large files skipped: {self.stats['large_files_skipped']}\n")
            f.write(f"Encoding errors: {self.stats['encoding_errors']}\n")
            f.write(f"Total characters: {self.stats['total_characters']:,}\n")
            f.write(f"Total lines: {self.stats['total_lines']:,}\n")
            f.write(f"Total files found: {file_tree['total_files']}\n")
            f.write(f"Total directories: {file_tree['total_dirs']}\n\n")

            # File tree
            f.write("REPOSITORY STRUCTURE:\n")
            f.write("-" * 40 + "\n")
            f.write(file_tree["tree"] + "\n\n")

            # File contents
            f.write("FILE CONTENTS:\n")
            f.write("=" * 80 + "\n\n")

            for file_path, content in sorted(text_content.items()):
                f.write(f"FILE: {file_path}\n")
                f.write("-" * len(f"FILE: {file_path}") + "\n")
                f.write(content)
                f.write("\n\n" + "=" * 80 + "\n\n")

        logger.info(f"Output written to: {output_file}")
        return output_file

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"