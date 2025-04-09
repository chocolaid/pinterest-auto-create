#!/usr/bin/env python
import os
import sys
import json
import argparse
import logging
from batch_account_creator import BatchAccountCreator, UserGenerator, ProxyHandler
from pinterest_account_creator import PinterestAccountCreator

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
            "max_delay": 120
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
    """Set up command line argument parser
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Pinterest Account Creator Automation")
    
    # General options
    parser.add_argument("-c", "--config", type=str, default="config.json",
                        help="Path to configuration file")
    parser.add_argument("-n", "--num-accounts", type=int,
                        help="Number of accounts to create")
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode (no browser UI)")
    
    # Proxy options
    proxy_group = parser.add_argument_group("Proxy Options")
    proxy_group.add_argument("--use-proxy", action="store_true",
                            help="Use proxies for account creation")
    proxy_group.add_argument("--proxy-file", type=str,
                            help="Path to file containing proxies")
    
    # User data options
    user_group = parser.add_argument_group("User Data Options")
    user_group.add_argument("--use-custom-data", action="store_true",
                           help="Use custom user data for account creation")
    user_group.add_argument("--data-file", type=str,
                           help="Path to file containing custom user data")
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("--output-file", type=str,
                             help="Path to output file for created accounts")
    output_group.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                             help="Logging level")
    
    return parser

def update_config_from_args(config, args):
    """Update configuration with command line arguments
    
    Args:
        config (dict): Configuration dictionary
        args (argparse.Namespace): Command line arguments
        
    Returns:
        dict: Updated configuration dictionary
    """
    # Update account creation settings
    if args.num_accounts is not None:
        config["account_creation"]["num_accounts"] = args.num_accounts
    if args.headless:
        config["account_creation"]["headless"] = True
    
    # Update proxy settings
    if args.use_proxy:
        config["proxy"]["use_proxy"] = True
    if args.proxy_file:
        config["proxy"]["proxy_file"] = args.proxy_file
    
    # Update user data settings
    if args.use_custom_data:
        config["user_data"]["use_custom_data"] = True
    if args.data_file:
        config["user_data"]["data_file"] = args.data_file
    
    # Update output settings
    if args.output_file:
        config["output"]["output_file"] = args.output_file
    if args.log_level:
        config["output"]["log_level"] = args.log_level
        # Update logging level
        numeric_level = getattr(logging, args.log_level)
        logging.getLogger().setLevel(numeric_level)
    
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
    """Main function to run the Pinterest account creator"""
    try:
        # Parse command line arguments
        parser = setup_argument_parser()
        args = parser.parse_args()
        
        # Load configuration
        config = load_config(args.config)
        
        # Update configuration with command line arguments
        config = update_config_from_args(config, args)
        
        # Save updated configuration
        save_config(config, args.config)
        
        # Set up batch account creator
        batch_creator = setup_batch_creator(config)
        
        # Display configuration
        print("\n" + "=" * 50)
        print("PINTEREST ACCOUNT CREATOR")
        print("=" * 50)
        print(f"Number of accounts to create: {config['account_creation']['num_accounts']}")
        print(f"Headless mode: {config['account_creation']['headless']}")
        print(f"Using proxies: {config['proxy']['use_proxy']}")
        print(f"Using custom user data: {config['user_data']['use_custom_data']}")
        print("=" * 50)
        print("Starting account creation...\n")
        
        # Create accounts
        stats = batch_creator.create_accounts()
        
        # Display summary
        display_summary(stats)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()