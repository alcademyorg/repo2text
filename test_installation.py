#!/usr/bin/env python3
"""
Test script to verify repo2text installation
"""

import sys
import importlib.util


def test_imports():
    """Test if all required modules can be imported"""

    required_modules = [
        "click",
        "git",
        "magic",
        "chardet",
        "repo2text.cli",
        "repo2text.core",
        "repo2text.utils",
    ]

    print("Testing module imports...")

    for module in required_modules:
        try:
            if importlib.util.find_spec(module):
                print(f"✓ {module}")
            else:
                print(f"✗ {module} - Not found")
                return False
        except ImportError as e:
            print(f"✗ {module} - Import error: {e}")
            return False

    return True


def test_basic_functionality():
    """Test basic functionality"""

    print("\nTesting basic functionality...")

    try:
        from repo2text.utils import validate_repo_url, sanitize_filename

        # Test URL validation
        valid_urls = [
            "https://github.com/user/repo",
            "https://gitlab.com/user/repo",
        ]

        invalid_urls = [
            "not-a-url",
            "https://example.com/not-a-repo",
        ]

        for url in valid_urls:
            if validate_repo_url(url):
                print(f"✓ URL validation: {url}")
            else:
                print(f"✗ URL validation failed: {url}")
                return False

        for url in invalid_urls:
            if not validate_repo_url(url):
                print(f"✓ URL rejection: {url}")
            else:
                print(f"✗ URL should be rejected: {url}")
                return False

        # Test filename sanitization
        test_filename = "test<>file|name?.txt"
        sanitized = sanitize_filename(test_filename)
        if sanitized == "test__file_name_.txt":
            print(f"✓ Filename sanitization: {test_filename} -> {sanitized}")
        else:
            print(f"✗ Filename sanitization failed: {test_filename} -> {sanitized}")
            return False

        return True

    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False


def main():
    """Run all tests"""

    print("repo2text Installation Test")
    print("=" * 40)

    # Test imports
    if not test_imports():
        print("\n✗ Import tests failed!")
        sys.exit(1)

    # Test basic functionality
    if not test_basic_functionality():
        print("\n✗ Functionality tests failed!")
        sys.exit(1)

    print("\n✓ All tests passed!")
    print("\nInstallation appears to be working correctly.")
    print("You can now use 'repo2text' command or import the library.")


if __name__ == "__main__":
    main()