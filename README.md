# Pinterest Auto Account Creator

A tool to automate Pinterest account creation with temporary email verification.

## Features

- Create Pinterest accounts automatically
- Use temporary email for verification
- Support for proxies
- Batch account creation
- Configurable delays and retries
- Account information saved to JSON file

## Requirements

- Python 3.8+
- Chrome browser installed
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository
2. Install required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

To create a single Pinterest account with temporary email verification:

```bash
python test_account_creation.py
```

### Batch Account Creation

To create multiple accounts:

```bash
python test_account_creation.py --num-accounts 5
```

### Using Proxies

To use proxies for account creation:

```bash
python test_account_creation.py --use-proxy --proxy-file proxies.txt
```

### Running in Headless Mode

To run browsers in headless mode (no visible browser windows):

```bash
python test_account_creation.py --headless
```

### Full Options

```
usage: test_account_creation.py [-h] [--headless] [--use-proxy] [--proxy-file PROXY_FILE]
                              [--num-accounts NUM_ACCOUNTS] [--output-file OUTPUT_FILE]
                              [--min-delay MIN_DELAY] [--max-delay MAX_DELAY]
                              [--max-retries MAX_RETRIES] [--verify-timeout VERIFY_TIMEOUT]

Test Pinterest account creation with temporary mail verification

options:
  -h, --help            show this help message and exit
  --headless            Run browser in headless mode
  --use-proxy           Use proxy for account creation
  --proxy-file PROXY_FILE
                        File containing list of proxies
  --num-accounts NUM_ACCOUNTS
                        Number of accounts to create
  --output-file OUTPUT_FILE
                        Output file for created accounts
  --min-delay MIN_DELAY
                        Minimum delay between account creations (seconds)
  --max-delay MAX_DELAY
                        Maximum delay between account creations (seconds)
  --max-retries MAX_RETRIES
                        Maximum number of retries per account
  --verify-timeout VERIFY_TIMEOUT
                        Timeout for email verification (seconds)
```

## Proxy Format

Proxies in the proxy file should be in one of these formats:

```
http://ip:port
http://username:password@ip:port
ip:port
```

## Output

Account information is saved to `accounts.json` by default. The file contains an array of account objects with the following fields:

- email
- password
- username
- first_name
- last_name
- age
- gender
- created_at
- proxy (if used)

## Troubleshooting

- Check the logs in the `logs` directory for detailed information.
- If you encounter issues with Chrome driver, try reinstalling Chrome to the latest version.
- Make sure your internet connection and proxies (if used) are working properly.

## License

This project is for educational purposes only.