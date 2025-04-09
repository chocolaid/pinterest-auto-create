# Pinterest Account Creator Automation

A comprehensive Python-based solution for automating Pinterest account creation with advanced features including proxy support, CAPTCHA solving, and email verification.

## Features

- Automated Pinterest account creation
- Random user information generation with customizable data
- Proxy support for avoiding IP restrictions
- CAPTCHA solving capabilities (manual and API-based)
- Email verification for created accounts
- Headless mode option for running without a visible browser
- Detailed logging and statistics
- Error handling and retry mechanisms

## Requirements

- Python 3.7+
- Chrome browser installed
- Internet connection

## Installation

1. Clone or download this repository
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Linux/Mac
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application uses a JSON configuration file (`config.json`) to control its behavior. You can modify this file directly or use command-line arguments to override settings.

### Sample Configuration

```json
{
    "account_creation": {
        "num_accounts": 5,
        "headless": false,
        "verify_success": true,
        "max_retries": 3,
        "min_delay": 30,
        "max_delay": 120
    },
    "proxy": {
        "use_proxy": true,
        "proxy_file": "proxies.txt",
        "proxy_list": [],
        "proxy_api_url": null,
        "proxy_api_key": null
    },
    "user_data": {
        "use_custom_data": true,
        "data_file": "user_data.json",
        "email_verification": false,
        "email_passwords": {
            "gmail.com": "your_gmail_password",
            "yahoo.com": "your_yahoo_password",
            "outlook.com": "your_outlook_password"
        }
    },
    "captcha": {
        "use_solver": false,
        "service": "2captcha",
        "api_key": null
    },
    "output": {
        "output_file": "pinterest_accounts.json",
        "log_level": "INFO"
    }
}
```

### Proxy Configuration

The application supports using proxies to avoid IP restrictions. You can provide proxies in a text file (one proxy per line) in the following formats:

```
http://ip:port
http://username:password@ip:port
https://ip:port
socks5://ip:port
```

## Usage

### Basic Usage

To create Pinterest accounts with default settings:

```bash
python pinterest_automation.py
```

### Command-line Arguments

You can override configuration settings using command-line arguments:

```bash
python pinterest_automation.py --num-accounts 10 --headless --use-proxy --proxy-file proxies.txt
```

Available arguments:

- `-c, --config`: Path to configuration file (default: config.json)
- `-n, --num-accounts`: Number of accounts to create
- `--headless`: Run in headless mode (no browser UI)
- `--use-proxy`: Use proxies for account creation
- `--proxy-file`: Path to file containing proxies
- `--use-custom-data`: Use custom user data for account creation
- `--data-file`: Path to file containing custom user data
- `--verify-email`: Enable email verification
- `--use-captcha-solver`: Use CAPTCHA solving service
- `--captcha-api-key`: API key for CAPTCHA solving service
- `--captcha-service`: CAPTCHA solving service to use (2captcha or anticaptcha)
- `--output-file`: Path to output file for created accounts
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Legacy Usage

You can still use the original script for simple account creation:

```bash
python pinterest_account_creator.py
```

Custom user information can be provided:

```python
user_info = {
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe123",
    "email": "johndoe123@example.com",
    "password": "SecurePassword123!",
    "age": 30,
    "gender": "male"
}

success, result = creator.create_account(user_info=user_info)
```

## Components

### Main Modules

- `pinterest_automation.py`: Main entry point for the automation
- `pinterest_account_creator.py`: Core functionality for creating Pinterest accounts
- `batch_account_creator.py`: Handles batch creation of multiple accounts
- `email_verification.py`: Handles email verification for created accounts
- `captcha_solver.py`: Provides CAPTCHA solving capabilities

### Helper Classes

- `UserGenerator`: Generates random user information
- `ProxyHandler`: Manages proxy rotation
- `EmailVerifier`: Verifies email addresses
- `CaptchaSolver`: Solves CAPTCHAs using various methods

## Output

Created accounts are saved in both JSON and text formats:

- `pinterest_accounts.json`: Contains detailed account information in JSON format
- `pinterest_accounts.txt`: Human-readable text file with account details

## Troubleshooting

### Common Issues

1. **Selenium WebDriver errors**: Make sure you have the latest version of Chrome installed and that the webdriver-manager package is up to date.

2. **Proxy errors**: Verify that your proxies are working and properly formatted.

3. **CAPTCHA solving failures**: If using a CAPTCHA solving service, check that your API key is valid and has sufficient balance.

4. **Email verification failures**: Ensure that the email provider allows IMAP access and that the credentials are correct.

### Logs

Detailed logs are saved to `pinterest_automation.log`. Check this file for error messages and debugging information.

## Legal Disclaimer

This tool is provided for educational purposes only. Using this tool to create multiple Pinterest accounts may violate Pinterest's Terms of Service. Use at your own risk.

## License

This project is licensed under the MIT License - see the LICENSE file for details.