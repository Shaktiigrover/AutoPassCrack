# AutoPassCrack

[![Code Size](https://img.shields.io/github/languages/code-size/HenryLok0/autopasscrack?style=flat-square&logo=github)](https://github.com/HenryLok0/autopasscrack)
![PyPI - Version](https://img.shields.io/pypi/v/autopasscrack)

[![MIT License](https://img.shields.io/github/license/HenryLok0/autopasscrack?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/HenryLok0/autopasscrack?style=flat-square)](https://github.com/HenryLok0/autopasscrack/stargazers)

Auto brute force web login forms tool

## Installation

### Create and activate a virtual environment

```bash
# Create a new virtual environment (named venv)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install dependencies

```bash
pip install autopasscrack
```

## Usage

### Command Line

```bash
# Basic usage with only URL (auto password generation if no file found)
autopasscrack https://example.com/login

# Specify username and password file
autopasscrack https://example.com/login --username myuser --passwords passwords.txt

# Specify only password file (no username)
autopasscrack https://example.com/login --passwords passwords.txt

# Specify only password string (no username, try all usernames)
autopasscrack https://example.com/login --passwords Password123

# Specify only password, use multiple candidates (comma separated, no username)
autopasscrack https://example.com/login --passwords "Password123,abc123,letmein"

# Specify only username (use auto password generation)
autopasscrack https://example.com/login --username myuser

# Use multiple parallel browser windows (e.g., 4 workers)
autopasscrack https://example.com/login --workers 4

# Auto-generate all passwords up to a maximum length (e.g., 6)
autopasscrack https://example.com/login --max-length 6

# Use both workers and max-length (e.g., try all 6, 5, 4, 3, 2, 1 length passwords in parallel)
autopasscrack https://example.com/login --workers 2 --max-length 6

# Set delay between each password attempt to 0.1 seconds (faster testing)
autopasscrack https://example.com/login --delay 0.1
```

### Python API

```python
from autopasscrack.auto_brute import brute_force

brute_force(
    url="https://example.com/login",
    username="myuser",
    password_list=["123456", "password", "letmein"],
    delay=0.1  # Set delay between attempts to 0.1 seconds
)
```

## Features
- Auto-detects login form fields (username and/or password)
- Supports custom password file or auto-generates passwords (all upper/lowercase letters, digits, special symbols)
- Supports direct password string or comma-separated passwords via --passwords (no need for a file)
- Supports auto-generating usernames (all upper/lowercase letters, digits, special symbols) if only --passwords is given and --username is omitted
- Supports parallel browser windows with --workers
- If no password file is provided, will use `default_passwords/password.txt` if it exists, otherwise auto-generate passwords
- **When using auto-generated passwords or usernames, the tool will start from the specified `--max-length` and automatically try all shorter lengths down to 1**
- **You can use `--delay` to control the time (in seconds) between each password attempt (e.g., `--delay 0.1` for fast testing)**

## Warning
- For legal penetration testing and educational use only. **Do not use on unauthorized websites.**
- Requires ChromeDriver installed and in your PATH.
