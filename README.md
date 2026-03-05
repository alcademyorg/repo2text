# repo2text

A powerful Python CLI tool that clones GitHub/GitLab repositories and converts all non-binary files into a comprehensive text format for analysis, documentation, or AI processing.

## Features

- 🔐 **Secure Authentication**: Supports GitHub and GitLab personal access tokens
- 📁 **Smart File Detection**: Automatically identifies and skips binary files
- 🌳 **Repository Structure**: Generates visual directory tree representations
- 📊 **Processing Statistics**: Detailed reports on files processed, skipped, and errors
- 🎯 **Configurable Limits**: Set maximum file sizes to process
- 📝 **Comprehensive Output**: Single text file containing all repository content
- 🧹 **Clean Workspace**: Optional cleanup of cloned repositories
- 🔍 **Verbose Logging**: Detailed logging for debugging and monitoring

## Installation

### Prerequisites

- Python 3.7 or higher
- Git installed on your system
- libmagic library (for file type detection)

#### Installing libmagic

**macOS:**

```bash
brew install libmagic
```

**Ubuntu/Debian:**

```bash
sudo apt-get install libmagic1
```

**Windows:**

```bash
pip install python-magic-bin
```

### Install repo2text

1. **Clone this repository:**

```bash
git clone https://github.com/yourusername/repo2text.git
cd repo2text
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Install the package:**

```bash
pip install -e .
```

## Usage

### Basic Usage

```bash
# For public repositories (no token required)
repo2text -r https://github.com/user/public-repository

# For private repositories (token required)
repo2text -t YOUR_TOKEN -r https://github.com/user/private-repository

# Specific branch (public repository)
repo2text -r https://github.com/user/public-repository -b develop

# Specific branch (private repository)
repo2text -t YOUR_TOKEN -r https://github.com/user/private-repository --branch feature/new-feature
```

### Advanced Usage

```bash
repo2text \
  --token YOUR_GITHUB_TOKEN \
  --repo-url https://github.com/user/repository \
  --branch develop \
  --output-dir ./analysis_results \
  --clone-dir ./temp_repos \
  --max-file-size 5 \
  --keep-clone \
  --verbose
```

### Command Line Options

| Option            | Short | Description                                                                | Default        |
| ----------------- | ----- | -------------------------------------------------------------------------- | -------------- |
| `--token`         | `-t`  | GitHub/GitLab personal access token (optional, required for private repos) | None           |
| `--repo-url`      | `-r`  | Repository URL (HTTPS format)                                              | Required       |
| `--branch`        | `-b`  | Specific branch to clone (optional)                                        | Default branch |
| `--output-dir`    | `-o`  | Output directory for text files                                            | `./output`     |
| `--clone-dir`     | `-c`  | Temporary directory for cloning                                            | `./temp_clone` |
| `--keep-clone`    |       | Keep cloned repository after processing                                    | `False`        |
| `--verbose`       | `-v`  | Enable verbose logging                                                     | `False`        |
| `--max-file-size` |       | Maximum file size in MB to process                                         | `10`           |

## Authentication

**Tokens are optional for public repositories but required for private repositories.**

### GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` scope for private repositories
3. For public repositories, no token is required

### GitLab Personal Access Token

1. Go to GitLab User Settings → Access Tokens
2. Create a token with `read_repository` scope
3. For private repositories, ensure you have access permissions

**Token Format Options:**

- **Simple token**: Just provide your personal access token (e.g., `glpat-xxxxxxxxxxxxxxxxxxxx`)
- **Username:token format**: Provide in the format `username:token` (e.g., `myusername:glpat-xxxxxxxxxxxxxxxxxxxx`)

When using the simple token format, the tool will automatically use `gitlab-ci-token` as the username. When using the username:token format, you can specify any username string.

## Output Format

The tool generates a comprehensive text file containing:

1. **Processing Statistics**: Number of files processed, skipped, and errors
2. **Repository Structure**: Visual directory tree with file sizes
3. **File Contents**: All non-binary files with clear separators

### Example Output Structure

```
================================================================================
REPOSITORY ANALYSIS: https://github.com/user/example-repo
================================================================================

PROCESSING STATISTICS:
----------------------------------------
Files processed: 25
Binary files skipped: 8
Large files skipped: 1
Encoding errors: 0
Total characters: 45,230
Total lines: 1,847
Total files found: 34
Total directories: 6

REPOSITORY STRUCTURE:
----------------------------------------
example-repo/
├── README.md (2.1KB)
├── requirements.txt (156B)
├── src/
│   ├── main.py (3.4KB)
│   └── utils.py (1.8KB)
└── tests/
    └── test_main.py (2.0KB)

FILE CONTENTS:
================================================================================

FILE: README.md
---------------
# Example Repository
This is an example repository...

================================================================================

FILE: requirements.txt
----------------------
requests>=2.28.0
click>=8.0.0

================================================================================
```

## Supported Platforms

- **GitHub**: github.com repositories
- **GitLab**: gitlab.com and custom GitLab instances
- **File Types**: All text-based files (source code, documentation, configuration files, etc.)

## Branch Selection

The tool supports cloning specific branches of repositories:

- **Default Behavior**: If no branch is specified, the repository's default branch (usually `main` or `master`) is cloned
- **Branch Specification**: Use `--branch` or `-b` to specify a specific branch name
- **Error Handling**: If the specified branch doesn't exist, the tool will provide a clear error message
- **Output Files**: When a branch is specified, the output filename will include the branch name (e.g., `repo_develop_analysis.txt`)

### Examples:

```bash
# Clone the main/master branch (default)
repo2text -r https://github.com/user/repository

# Clone a specific branch
repo2text -r https://github.com/user/repository -b develop
repo2text -r https://github.com/user/repository --branch feature/authentication

# Clone a specific branch with authentication
repo2text -t YOUR_TOKEN -r https://github.com/user/private-repo -b staging
```

## Binary File Detection

The tool uses multiple methods to identify binary files:

1. **File Extension**: Common binary extensions (.jpg, .png, .exe, .pdf, etc.)
2. **MIME Type**: Uses libmagic to detect file types
3. **Null Byte Detection**: Scans for null bytes in file content
4. **Encoding Detection**: Attempts to decode files as text

## Error Handling

- **Authentication Errors**: Clear messages for token issues
- **Network Errors**: Handles connection problems gracefully
- **File Access Errors**: Skips files with permission issues
- **Encoding Errors**: Uses fallback encoding strategies

## Examples

### Analyze a Public Repository

```bash
# No token required for public repositories
repo2text -r https://github.com/torvalds/linux

# You can still use a token for public repositories if desired
repo2text -t ghp_your_token_here -r https://github.com/torvalds/linux
```

### Analyze a Private Repository

```bash
# Token required for private repositories
repo2text -t ghp_your_token_here -r https://github.com/user/private-repo
```

### Analyze with Custom Settings

```bash
# Using simple GitLab token
repo2text \
  -t glpat-your_gitlab_token \
  -r https://gitlab.com/user/project \
  -o ./project_analysis \
  --max-file-size 20 \
  --verbose

# Using username:token format for GitLab
repo2text \
  -t myusername:glpat-your_gitlab_token \
  -r https://gitlab.com/user/project \
  -o ./project_analysis \
  --max-file-size 20 \
  --verbose
```

### Keep Clone for Further Analysis

```bash
repo2text \
  -t your_token \
  -r https://github.com/user/repo \
  --keep-clone \
  --clone-dir ./repos/my_analysis
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**

   - Verify your token is correct and has necessary permissions
   - Check if the repository exists and you have access

2. **libmagic Not Found**

   - Install libmagic using your system package manager
   - On Windows, use `pip install python-magic-bin`

3. **Large Repository Timeouts**

   - Use `--max-file-size` to limit file processing
   - Consider using `--keep-clone` to avoid re-cloning

4. **Permission Errors**
   - Ensure write permissions for output and clone directories
   - Run with appropriate user permissions

### Debug Mode

Enable verbose logging to see detailed processing information:

```bash
repo2text -t your_token -r repo_url --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v1.1.0

- Added character count statistics
- Added line count statistics
- Enhanced processing statistics display
- Improved CLI output with detailed metrics

### v1.0.0

- Initial release
- GitHub and GitLab support
- Binary file detection
- Comprehensive text output
- CLI interface with multiple options
