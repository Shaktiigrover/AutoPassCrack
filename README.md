# AutoPassCrack

[![Code Size](https://img.shields.io/github/languages/code-size/HenryLok0/autopasscrack?style=flat-square&logo=github)](https://github.com/HenryLok0/autopasscrack)
![PyPI - Version](https://img.shields.io/pypi/v/autopasscrack)

[![MIT License](https://img.shields.io/github/license/HenryLok0/autopasscrack?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/HenryLok0/autopasscrack?style=flat-square)](https://github.com/HenryLok0/autopasscrack/stargazers)

Auto brute force web login forms tool

## Installation

### Create and activate a virtual environment

```bash
python -m venv venv
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

### Command Line Examples

#### 1. **Quick Start (auto password generation)**
```bash
autopasscrack https://example.com/login
```
- If neither username nor password is specified, autopasscrack will try **all possible username/password combinations** (very slow, for research/testing only).

#### 2. **Specify username, auto-generate passwords**
```bash
autopasscrack https://example.com/login --username myuser
```
- Tries all possible passwords for the given username.

#### 3. **Specify password(s), auto-generate usernames**
```bash
autopasscrack https://example.com/login --passwords Password123
```
- Tries all possible usernames with the given password.
- You can use a file or comma-separated passwords:
  - `--passwords passwords.txt`
  - `--passwords "Password123,abc123,letmein"`

#### 4. **Specify both username and password(s)**
```bash
autopasscrack https://example.com/login --username myuser --passwords passwords.txt
```
- Tries all passwords in the file for the given username.

#### 5. **Parallel mode (multiple browser windows)**
```bash
autopasscrack https://example.com/login --username myuser --passwords passwords.txt --workers 4
```
- Use multiple browser windows for faster brute force.

#### 6. **Limit password/username length**
```bash
autopasscrack https://example.com/login --username myuser --max-length 6
```
- Auto-generate all passwords up to a maximum length (default: 4, max: 20).

#### 7. **Set delay between attempts**
```bash
autopasscrack https://example.com/login --username myuser --delay 0.1
```
- Set delay (in seconds) between each attempt (default: 2).

#### 8. **Specify success URL for accurate detection**
```bash
autopasscrack https://example.com/login --username myuser --passwords Password123 --success_url https://example.com/success
```
- Use this if the login is only successful when redirected to a specific URL.

### Python API Example

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
- Supports **full auto mode**: if neither username nor password is given, tries all possible username/password combinations (very slow, for research/testing only)
- Supports parallel browser windows with --workers
- If no password file is provided, will use `default_passwords/password.txt` if it exists, otherwise auto-generate passwords
- **When using auto-generated passwords or usernames, the tool will start from the specified `--max-length` and automatically try all shorter lengths down to 1**
- **You can use `--delay` to control the time (in seconds) between each password attempt (e.g., `--delay 0.1` for fast testing)**

## Warning
- For legal penetration testing and educational use only. **Do not use on unauthorized websites.**
- Requires ChromeDriver installed and in your PATH.
