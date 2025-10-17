#!/usr/bin/env python
import os
import sys
import json
import argparse
import logging
from batch_account_creator import BatchAccountCreator, UserGenerator, ProxyHandler
from pinterest_account_creator import PinterestAccountCreator
from account_manager import AccountManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pinterest_automation.log"),
        logging.StreamHandler()
    ]
)

def load_config(config_file="config.json"):
    """Load configuration from JSON file
    
    Args:
        config_file (str): Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            logging.info(f"Loaded configuration from {config_file}")
            return config
        else:
            logging.warning(f"Config file {config_file} not found, using default settings")
            return create_default_config()
    except Exception as e:
        logging.error(f"Error loading config: {str(e)}")
        return create_default_config()

def create_default_config():
    """Create default configuration
    
    Returns:
        dict: Default configuration dictionary
    """
    return {
        "account_creation": {
            "num_accounts": 1,
            "headless": False,
            "verify_success": True,
            "max_retries": 3,
            "min_delay": 30,
            "max_delay": 120,
            "use_temp_mail": True  # Default to using temp mail
        },
        "proxy": {
            "use_proxy": False,
            "proxy_file": "proxies.txt",
            "proxy_list": [],
            "proxy_api_url": None,
            "proxy_api_key": None
        },
        "user_data": {
            "use_custom_data": False,
            "data_file": "user_data.json"
        },
        "output": {
            "output_file": "pinterest_accounts.json",
            "log_level": "INFO"
        }
    }

def save_config(config, config_file="config.json"):
    """Save configuration to JSON file
    
    Args:
        config (dict): Configuration dictionary
        config_file (str): Path to the configuration file
    """
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        logging.info(f"Saved configuration to {config_file}")
    except Exception as e:
        logging.error(f"Error saving config: {str(e)}")

def setup_argument_parser():
    """Set up command line argument parser"""
    parser = argparse.ArgumentParser(description="Pinterest Account Creator")
    
    # General options
    parser.add_argument("--config", type=str, default="config.json", help="Path to configuration file")
    parser.add_argument("--num-accounts", type=int, help="Number of accounts to create")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    # Proxy options
    parser.add_argument("--use-proxy", action="store_true", help="Use proxies")
    parser.add_argument("--proxy-file", type=str, help="Path to proxy file")
    parser.add_argument("--proxy-api-url", type=str, help="URL for proxy API")
    parser.add_argument("--proxy-api-key", type=str, help="API key for proxy API")
    
    # Email verification options
    parser.add_argument("--use-temp-mail", action="store_true", help="Use temporary email for verification")
    parser.add_argument("--verify-timeout", type=int, help="Timeout for email verification in seconds")
    
    # Output options
    parser.add_argument("--output-file", type=str, help="Path to output file")
    
    # Other options
    parser.add_argument("--min-delay", type=int, help="Minimum delay between account creations in seconds")
    parser.add_argument("--max-delay", type=int, help="Maximum delay between account creations in seconds")
    parser.add_argument("--max-retries", type=int, help="Maximum number of retries per account")
    
    return parser

def update_config_from_args(config, args):
    """Update configuration with command line arguments
    
    Args:
        config (dict): Configuration dictionary
        args (argparse.Namespace): Command line arguments
        
    Returns:
        dict: Updated configuration dictionary
    """
    # Update general settings
    if args.num_accounts:
        config["batch"]["num_accounts"] = args.num_accounts
    if args.headless:
        config["account_creation"]["headless"] = True
    if args.use_temp_mail:
        config["account_creation"]["use_temp_mail"] = True
    
    # Update proxy settings
    if args.use_proxy:
        config["proxy"]["enabled"] = True
    if args.proxy_file:
        config["proxy"]["proxy_file"] = args.proxy_file
    if args.proxy_api_url:
        config["proxy"]["proxy_api_url"] = args.proxy_api_url
    if args.proxy_api_key:
        config["proxy"]["proxy_api_key"] = args.proxy_api_key
    
    # Update verification settings
    if args.verify_timeout:
        config["verification"]["timeout"] = args.verify_timeout
    
    # Update output settings
    if args.output_file:
        config["output"]["accounts_file"] = args.output_file
    
    # Update timing settings
    if args.min_delay:
        config["batch"]["min_delay"] = args.min_delay
    if args.max_delay:
        config["batch"]["max_delay"] = args.max_delay
    if args.max_retries:
        config["batch"]["max_retries"] = args.max_retries
    
    return config

def setup_batch_creator(config):
    """Set up the batch account creator with configuration
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        BatchAccountCreator: Configured batch account creator
    """
    # Prepare batch creator configuration
    batch_config = {
        "num_accounts": config["account_creation"]["num_accounts"],
        "headless": config["account_creation"]["headless"],
        "max_retries": config["account_creation"]["max_retries"],
        "min_delay": config["account_creation"]["min_delay"],
        "max_delay": config["account_creation"]["max_delay"],
        "use_proxy": config["proxy"]["use_proxy"],
        "use_temp_mail": config["account_creation"]["use_temp_mail"],  # Add temp mail setting
        "proxy_file": config["proxy"]["proxy_file"],
        "proxy_list": config["proxy"]["proxy_list"],
        "proxy_api_url": config["proxy"]["proxy_api_url"],
        "proxy_api_key": config["proxy"]["proxy_api_key"]
    }
    
    # Set up user generator if using custom data
    user_generator = None
    if config["user_data"]["use_custom_data"]:
        user_generator = UserGenerator(data_file=config["user_data"]["data_file"])
    
    # Set up proxy handler if using proxies
    proxy_handler = None
    if config["proxy"]["use_proxy"]:
        proxy_handler = ProxyHandler(
            proxy_file=config["proxy"]["proxy_file"],
            proxy_list=config["proxy"]["proxy_list"],
            proxy_api_url=config["proxy"]["proxy_api_url"],
            proxy_api_key=config["proxy"]["proxy_api_key"]
        )
    
    # Create batch account creator
    batch_creator = BatchAccountCreator(config=batch_config)
    
    # Set user generator and proxy handler if available
    if user_generator:
        batch_creator.user_generator = user_generator
    if proxy_handler:
        batch_creator.proxy_handler = proxy_handler
    
    return batch_creator

def display_summary(stats):
    """Display summary of account creation process
    
    Args:
        stats (dict): Statistics from batch account creation
    """
    print("\n" + "=" * 50)
    print("PINTEREST ACCOUNT CREATION SUMMARY")
    print("=" * 50)
    print(f"Start Time: {stats['start_time']}")
    print(f"End Time: {stats['end_time']}")
    print(f"Duration: {stats['duration']:.2f} minutes")
    print(f"Accounts Created: {stats['success']}")
    print(f"Failed Attempts: {stats['failed']}")
    print(f"Success Rate: {(stats['success'] / (stats['success'] + stats['failed'])) * 100:.2f}%")
    print("=" * 50)
    print(f"Created accounts saved to: {os.path.abspath('pinterest_accounts.json')}")
    print("=" * 50)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Pinterest Account Creator')
    parser.add_argument('--creation-threads', type=int, default=2,
                      help='Number of account creation threads')
    parser.add_argument('--verification-threads', type=int, default=3,
                      help='Number of verification threads')
    parser.add_argument('--headless', action='store_true',
                      help='Run browsers in headless mode')
    parser.add_argument('--use-proxy', action='store_true',
                      help='Use proxy for account creation')
    parser.add_argument('--proxy', type=str,
                      help='Proxy address in format http://ip:port')
    parser.add_argument('--use-temp-mail', action='store_true', default=True,
                      help='Use temp mail for verification')
    
    args = parser.parse_args()
    
    try:
        # Create account manager
        manager = AccountManager(
            num_creation_threads=args.creation_threads,
            num_verification_threads=args.verification_threads,
            headless=args.headless,
            use_proxy=args.use_proxy,
            proxy=args.proxy,
            use_temp_mail=args.use_temp_mail
        )
        
        # Start the process
        manager.start()
        
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        manager.stop()
    except Exception as e:
        print(f"Error: {str(e)}")
        manager.stop()

if __name__ == "__main__":
    main()