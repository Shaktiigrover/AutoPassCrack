# AutoPassCrack

[![Code Size](https://img.shields.io/github/languages/code-size/HenryLok0/autopasscrack?style=flat-square&logo=github)](https://github.com/HenryLok0/autopasscrack)
![PyPI - Version](https://img.shields.io/pypi/v/autopasscrack)

[![MIT License](https://img.shields.io/github/license/HenryLok0/autopasscrack?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/HenryLok0/autopasscrack?style=flat-square)](https://github.com/HenryLok0/autopasscrack/stargazers)

A professional, flexible, and user-friendly tool for automated brute-forcing of web login forms. Supports advanced field detection, custom password/username generation, parallel execution, and more.

## Installation

### Create and activate a virtual environment

```bash
-m venv venv
source venv/bin/activate         # On Windows: venv\Scripts\activate
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

#### 9. **Custom charset, blacklist, whitelist for password/username generation**
```bash
autopasscrack https://example.com/login --username myuser --charset abcdef1234 --blacklist f --whitelist abc123
```
- Use a custom charset, exclude or include specific characters for brute force.

#### 10. **Prioritize common passwords/usernames**
```bash
autopasscrack https://example.com/login --common-passwords common_pw.txt --common-usernames common_users.txt
```
- Try common passwords/usernames first before brute force.

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

## Advanced Login Field Detection
- The tool now detects all possible username/email fields based on type, name, id, placeholder, and aria-label attributes (keywords: user, email, login, account), and pairs them with all password fields. This increases compatibility with various login forms.

## Password Strength Test Tool
- A simple password strength checker is available at `docs/index.html`. Open it in your browser to test password strength (length, upper/lowercase, digit, symbol).

## Features
- Auto-detects all possible login form field pairs (username/email and password) using advanced heuristics
- Supports custom password file or auto-generates passwords (all upper/lowercase letters, digits, special symbols)
- Supports direct password string or comma-separated passwords via --passwords (no need for a file)
- Supports auto-generating usernames (all upper/lowercase letters, digits, special symbols) if only --passwords is given and --username is omitted
- Supports **full auto mode**: if neither username nor password is given, tries all possible username/password combinations (very slow, for research/testing only)
- Supports parallel browser windows with --workers
- If no password file is provided, will use `default_passwords/password.txt` if it exists, otherwise auto-generate passwords
- **Flexible brute force charset**: use `--charset`, `--blacklist`, `--whitelist` to control which characters are used
- **Prioritize common passwords/usernames**: use `--common-passwords` and `--common-usernames` to try common values first
- **When using auto-generated passwords or usernames, the tool will start from the specified `--max-length` and automatically try all shorter lengths down to 1**
- **You can use `--delay` to control the time (in seconds) between each password attempt (e.g., `--delay 0.1` for fast testing)**
- Includes a password strength HTML tool in `/docs/index.html`


## Resume & Progress Display

### Resume (Interrupted Session)
- You can use `--resume` to continue from where you left off if the process was interrupted (supports both single and multi-worker modes).
- Progress is automatically saved to `.autopasscrack_resume.json`.
- When resuming, only untried passwords/usernames will be distributed to workers, ensuring no duplicates or missing attempts.
- After a successful run, the resume file is automatically cleared.

#### Example:
```bash
autopasscrack https://example.com/login --username myuser --passwords passwords.txt --workers 4 --resume
```
- If interrupted, rerun with `--resume` to continue from last progress.

### CLI Progress Display
- The tool shows real-time progress, including current attempt, total attempts, percentage, elapsed time, and estimated time left.
- Example output:
  ```
  Progress: 3/100 (3.00%), Elapsed: 2.1s, ETA: 67.9s
  ```

## Warning
- For legal penetration testing and educational use only. **Do not use on unauthorized websites.**
- Requires ChromeDriver installed and in your PATH.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support

If you have questions or need help, please open an issue on GitHub.

Thank you to all contributors and the open-source community for your support.