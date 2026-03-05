"""
Utility functions for repo2text
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import magic
import chardet


def validate_repo_url(url: str) -> bool:
    """Validate if the URL is a valid GitHub or GitLab repository URL"""

    try:
        parsed = urlparse(url)

        # Check if it's a valid URL
        if not parsed.scheme or not parsed.netloc:
            return False

        # Check if it's GitHub or GitLab
        valid_hosts = [
            "github.com",
            "gitlab.com",
        ]

        # Also allow custom GitLab instances
        if (
            any(host in parsed.netloc for host in valid_hosts)
            or "gitlab" in parsed.netloc
        ):
            # Check if path looks like a repository path
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2:
                return True

        return False

    except Exception:
        return False


def is_binary_file(file_path: Path) -> bool:
    """
    Determine if a file is binary using multiple methods

    Args:
        file_path: Path to the file to check

    Returns:
        True if file is binary, False otherwise
    """

    try:
        # Method 1: Check file extension
        binary_extensions = {
            # Images
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".ico",
            ".svg",
            # Videos
            ".mp4",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".mkv",
            # Audio
            ".mp3",
            ".wav",
            ".flac",
            ".aac",
            ".ogg",
            ".wma",
            # Archives
            ".zip",
            ".rar",
            ".7z",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            # Executables
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".bin",
            # Documents
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            # Fonts
            ".ttf",
            ".otf",
            ".woff",
            ".woff2",
            # Other binary formats
            ".pyc",
            ".pyo",
            ".class",
            ".jar",
            ".war",
        }

        if file_path.suffix.lower() in binary_extensions:
            return True

        # Method 2: Use python-magic if available
        try:
            mime_type = magic.from_file(str(file_path), mime=True)
            if mime_type:
                # Text MIME types
                text_types = [
                    "text/",
                    "application/json",
                    "application/xml",
                    "application/javascript",
                    "application/x-sh",
                    "application/x-python",
                ]

                if any(mime_type.startswith(t) for t in text_types):
                    return False

                # Known binary types
                binary_types = [
                    "image/",
                    "video/",
                    "audio/",
                    "application/octet-stream",
                    "application/pdf",
                    "application/zip",
                ]

                if any(mime_type.startswith(t) for t in binary_types):
                    return True
        except:
            pass

        # Method 3: Check for null bytes in the first chunk
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)  # Read first 8KB
                if b"\x00" in chunk:
                    return True
        except:
            return True  # If we can't read it, assume it's binary

        # Method 4: Try to decode as text
        try:
            with open(file_path, "rb") as f:
                sample = f.read(1024)  # Read first 1KB

            # Try to detect encoding
            encoding_info = chardet.detect(sample)
            if encoding_info["confidence"] < 0.5:
                return True

            # Try to decode
            sample.decode(encoding_info["encoding"] or "utf-8")
            return False

        except (UnicodeDecodeError, LookupError):
            return True

        return False

    except Exception:
        return True  # If anything fails, assume binary


def get_file_encoding(file_path: Path) -> Optional[str]:
    """
    Detect the encoding of a text file

    Args:
        file_path: Path to the file

    Returns:
        Detected encoding or None if detection fails
    """

    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()

        result = chardet.detect(raw_data)
        return result.get("encoding")

    except Exception:
        return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to be safe for filesystem use

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """

    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip(" .")

    # Ensure it's not empty
    if not filename:
        filename = "unnamed"

    # Limit length
    if len(filename) > 200:
        filename = filename[:200]

    return filename


def setup_logging(verbose: bool = False):
    """
    Setup logging configuration

    Args:
        verbose: Enable verbose logging
    """

    level = logging.DEBUG if verbose else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # Reduce noise from git library
    logging.getLogger("git").setLevel(logging.WARNING)


def create_directory_tree(
    path: Path, prefix: str = "", max_depth: int = 10, current_depth: int = 0
) -> str:
    """
    Create a visual directory tree representation

    Args:
        path: Root path to create tree from
        prefix: Current line prefix
        max_depth: Maximum depth to traverse
        current_depth: Current traversal depth

    Returns:
        String representation of directory tree
    """

    if current_depth >= max_depth:
        return f"{prefix}[Max depth reached]\n"

    try:
        items = list(path.iterdir())
        items.sort(key=lambda x: (x.is_file(), x.name.lower()))

        tree_str = ""

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "

            if item.is_dir():
                tree_str += f"{prefix}{current_prefix}{item.name}/\n"
                extension = "    " if is_last else "│   "
                tree_str += create_directory_tree(
                    item, prefix + extension, max_depth, current_depth + 1
                )
            else:
                try:
                    size = item.stat().st_size
                    size_str = format_bytes(size)
                    tree_str += f"{prefix}{current_prefix}{item.name} ({size_str})\n"
                except:
                    tree_str += f"{prefix}{current_prefix}{item.name}\n"

        return tree_str

    except PermissionError:
        return f"{prefix}[Permission Denied]\n"
    except Exception as e:
        return f"{prefix}[Error: {str(e)}]\n"


def format_bytes(size: int) -> str:
    """Format byte size in human readable format"""

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}PB"
