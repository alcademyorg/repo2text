from setuptools import setup, find_packages

setup(
    name="repo2text",
    version="1.1.0",
    description="A CLI tool to clone GitHub/GitLab repositories and convert non-binary files to text",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "GitPython>=3.1.0",
        "requests>=2.28.0",
        "python-magic>=0.4.27",
        "chardet>=5.0.0",
    ],
    entry_points={
        "console_scripts": [
            "repo2text=repo2text.cli:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
