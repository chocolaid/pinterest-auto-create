#!/usr/bin/env python
import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime

# Add current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_account_creator import PinterestAccountCreator
from email_verification import EmailVerifier
from utils.logger import setup_logger
from utils.proxy_manager import ProxyManager

# Setup logger
logger = setup_logger("test_account_creation")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test Pinterest account creation with temporary mail verification"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode"
    )
    parser.add_argument(
        "--use-proxy", action="store_true", help="Use proxy for account creation"
    )
    parser.add_argument(
        "--proxy-file", type=str, help="File containing list of proxies"
    )
    parser.add_argument(
        "--num-accounts", type=int, default=1, help="Number of accounts to create"
    )
    parser.add_argument(
        "--output-file", type=str, default="accounts.json", help="Output file for created accounts"
    )
    parser.add_argument(
        "--min-delay", type=int, default=10, help="Minimum delay between account creations (seconds)"
    )
    parser.add_argument(
        "--max-delay", type=int, default=30, help="Maximum delay between account creations (seconds)"
    )
    parser.add_argument(
        "--max-retries", type=int, default=3, help="Maximum number of retries per account"
    )
    parser.add_argument(
        "--verify-timeout", type=int, default=180, help="Timeout for email verification (seconds)"
    )
    
    return parser.parse_args()

def load_existing_accounts(output_file):
    """Load existing accounts from output file."""
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse {output_file}, starting with empty accounts list")
    return []

def save_accounts(accounts, output_file):
    """Save accounts to output file."""
    with open(output_file, 'w') as f:
        json.dump(accounts, f, indent=4)

def create_account(config, proxy=None, account_number=1, total_accounts=1):
    """Create a Pinterest account with temporary mail verification."""
    logger.info(f"Creating account {account_number}/{total_accounts}")
    
    # Initialize account creator with temp_mail=True
    creator = PinterestAccountCreator(
        headless=config.get("headless", True),
        proxy=proxy,
        use_temp_mail=True
    )
    
    try:
        # Create account
        success, account_data = creator.create_account()
        
        if not success:
            logger.error(f"Failed to create account {account_number}: {account_data}")
            return None
        
        # Add timestamp and metadata
        account_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        account_data["proxy"] = proxy
        
        logger.info(f"Successfully created account: {account_data['email']}")
        return account_data
        
    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        return None
    finally:
        creator.close()

def main():
    """Main function to run batch account creation."""
    args = parse_arguments()
    
    # Create config dictionary
    config = {
        "headless": args.headless,
        "use_proxy": args.use_proxy,
        "proxy_file": args.proxy_file,
        "num_accounts": args.num_accounts,
        "output_file": args.output_file,
        "min_delay": args.min_delay,
        "max_delay": args.max_delay,
        "max_retries": args.max_retries,
        "verify_timeout": args.verify_timeout
    }
    
    # Initialize proxy manager if needed
    proxy_manager = None
    if config.get("use_proxy") and config.get("proxy_file"):
        proxy_manager = ProxyManager(config.get("proxy_file"))
        proxies = proxy_manager.get_proxies()
        if not proxies:
            logger.error("No proxies available. Exiting.")
            return
        logger.info(f"Loaded {len(proxies)} proxies from {config.get('proxy_file')}")
    
    # Load existing accounts
    accounts = load_existing_accounts(config.get("output_file"))
    initial_count = len(accounts)
    
    # Create accounts
    success_count = 0
    for i in range(config.get("num_accounts")):
        retry_count = 0
        account_created = False
        
        while not account_created and retry_count < config.get("max_retries"):
            try:
                # Get proxy if needed
                proxy = None
                if proxy_manager:
                    proxy = proxy_manager.get_random_proxy()
                    logger.info(f"Using proxy: {proxy}")
                
                # Create account
                account_data = create_account(
                    config,
                    proxy=proxy,
                    account_number=i+1,
                    total_accounts=config.get("num_accounts")
                )
                
                if account_data:
                    accounts.append(account_data)
                    save_accounts(accounts, config.get("output_file"))
                    success_count += 1
                    account_created = True
                else:
                    retry_count += 1
                    logger.warning(f"Retrying account creation ({retry_count}/{config.get('max_retries')})")
            
            except Exception as e:
                retry_count += 1
                logger.error(f"Error during account creation: {str(e)}")
                logger.warning(f"Retrying account creation ({retry_count}/{config.get('max_retries')})")
        
        # Wait between account creations
        if i < config.get("num_accounts") - 1:
            delay = random.randint(config.get("min_delay"), config.get("max_delay"))
            logger.info(f"Waiting {delay} seconds before next account...")
            time.sleep(delay)
    
    # Print summary
    logger.info(f"Account creation completed.")
    logger.info(f"Created {success_count} new accounts out of {config.get('num_accounts')} attempts")
    logger.info(f"Total accounts: {len(accounts)} (including {initial_count} existing accounts)")
    logger.info(f"Accounts saved to {config.get('output_file')}")

if __name__ == "__main__":
    main() 