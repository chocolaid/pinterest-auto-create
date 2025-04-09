#!/usr/bin/env python
import os
import sys
import json
import time
import random
import logging
import argparse
from datetime import datetime
from batch_account_creator import BatchAccountCreator, UserGenerator, ProxyHandler
from pinterest_account_creator import PinterestAccountCreator
from email_verification import EmailVerifier
from captcha_solver import CaptchaSolver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pinterest_automation.log"),
        logging.StreamHandler()
    ]
)

class PinterestAutomation:
    """A comprehensive class to automate Pinterest account creation"""
    
    def __init__(self, config_file="config.json"):
        """Initialize the Pinterest automation
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.batch_creator = None
        self.email_verifier = None
        self.captcha_solver = None
        self.setup_components()
    
    def load_config(self):
        """Load configuration from JSON file
        
        Returns:
            dict: Configuration dictionary
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logging.info(f"Loaded configuration from {self.config_file}")
                return config
            else:
                logging.warning(f"Config file {self.config_file} not found, using default settings")
                return self.create_default_config()
        except Exception as e:
            logging.error(f"Error loading config: {str(e)}")
            return self.create_default_config()
    
    def create_default_config(self):
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
                "data_file": "user_data.json",
                "email_verification": False,
                "email_passwords": {}
            },
            "captcha": {
                "use_solver": False,
                "service": "2captcha",
                "api_key": None
            },
            "output": {
                "output_file": "pinterest_accounts.json",
                "log_level": "INFO"
            }
        }
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logging.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logging.error(f"Error saving config: {str(e)}")
    
    def setup_components(self):
        """Set up the automation components"""
        # Set up batch creator configuration
        batch_config = {
            "num_accounts": self.config["account_creation"]["num_accounts"],
            "headless": self.config["account_creation"]["headless"],
            "max_retries": self.config["account_creation"]["max_retries"],
            "min_delay": self.config["account_creation"]["min_delay"],
            "max_delay": self.config["account_creation"]["max_delay"],
            "use_proxy": self.config["proxy"]["use_proxy"],
            "proxy_file": self.config["proxy"]["proxy_file"],
            "proxy_list": self.config["proxy"]["proxy_list"],
            "proxy_api_url": self.config["proxy"]["proxy_api_url"],
            "proxy_api_key": self.config["proxy"]["proxy_api_key"]
        }
        
        # Set up user generator if using custom data
        user_generator = None
        if self.config["user_data"]["use_custom_data"]:
            user_generator = UserGenerator(data_file=self.config["user_data"]["data_file"])
        
        # Set up proxy handler if using proxies
        proxy_handler = None
        if self.config["proxy"]["use_proxy"]:
            proxy_handler = ProxyHandler(
                proxy_file=self.config["proxy"]["proxy_file"],
                proxy_list=self.config["proxy"]["proxy_list"],
                proxy_api_url=self.config["proxy"]["proxy_api_url"],
                proxy_api_key=self.config["proxy"]["proxy_api_key"]
            )
        
        # Create batch account creator
        self.batch_creator = BatchAccountCreator(config=batch_config)
        
        # Set user generator and proxy handler if available
        if user_generator:
            self.batch_creator.user_generator = user_generator
        if proxy_handler:
            self.batch_creator.proxy_handler = proxy_handler
        
        # Set up email verifier
        self.email_verifier = EmailVerifier(headless=self.config["account_creation"]["headless"])
        
        # Set up CAPTCHA solver if enabled
        if self.config["captcha"]["use_solver"]:
            self.captcha_solver = CaptchaSolver(
                api_key=self.config["captcha"]["api_key"],
                service=self.config["captcha"]["service"]
            )
    
    def run(self):
        """Run the Pinterest automation
        
        Returns:
            dict: Statistics about the account creation process
        """
        try:
            # Display configuration
            self._display_config()
            
            # Create accounts
            stats = self._create_accounts()
            
            # Display summary
            self._display_summary(stats)
            
            return stats
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return {"error": "Operation cancelled by user"}
        except Exception as e:
            logging.error(f"Error running automation: {str(e)}")
            return {"error": str(e)}
    
    def _display_config(self):
        """Display the current configuration"""
        print("\n" + "=" * 50)
        print("PINTEREST ACCOUNT CREATOR")
        print("=" * 50)
        print(f"Number of accounts to create: {self.config['account_creation']['num_accounts']}")
        print(f"Headless mode: {self.config['account_creation']['headless']}")
        print(f"Using proxies: {self.config['proxy']['use_proxy']}")
        print(f"Using custom user data: {self.config['user_data']['use_custom_data']}")
        print(f"Email verification: {self.config['user_data']['email_verification']}")
        print(f"Using CAPTCHA solver: {self.config['captcha']['use_solver']}")
        print("=" * 50)
        print("Starting account creation...\n")
    
    def _create_accounts(self):
        """Create Pinterest accounts with extended functionality
        
        Returns:
            dict: Statistics about the account creation process
        """
        stats = {
            "start_time": datetime.now(),
            "success": 0,
            "failed": 0,
            "verified": 0,
            "accounts": []
        }
        
        for i in range(self.config["account_creation"]["num_accounts"]):
            logging.info(f"Creating account {i+1} of {self.config['account_creation']['num_accounts']}")
            
            # Get proxy if using proxies
            proxy = None
            if self.config["proxy"]["use_proxy"] and self.batch_creator.proxy_handler:
                proxy = self.batch_creator.proxy_handler.get_random_proxy()
                if not proxy:
                    logging.warning("No proxy available, continuing without proxy")
            
            # Create account with retries
            account_created = False
            retries = 0
            
            while not account_created and retries < self.config["account_creation"]["max_retries"]:
                if retries > 0:
                    logging.info(f"Retry attempt {retries} for account {i+1}")
                    
                    # Get a new proxy for retry if available
                    if self.config["proxy"]["use_proxy"] and self.batch_creator.proxy_handler:
                        proxy = self.batch_creator.proxy_handler.get_next_proxy()
                
                # Generate user info
                user_info = self.batch_creator.user_generator.generate_user()
                
                # Create Pinterest account creator instance
                creator = PinterestAccountCreator(
                    headless=self.config["account_creation"]["headless"],
                    use_proxy=self.config["proxy"]["use_proxy"],
                    proxy=proxy
                )
                
                try:
                    # Inject CAPTCHA solver if available
                    if self.captcha_solver and self.config["captcha"]["use_solver"]:
                        creator.captcha_solver = self.captcha_solver
                    
                    # Create account
                    success, result = creator.create_account(user_info=user_info)
                    
                    if success:
                        logging.info(f"Successfully created account: {result['email']}")
                        
                        # Verify email if enabled
                        verified = False
                        if self.config["user_data"]["email_verification"]:
                            email = result["email"]
                            domain = email.split("@")[1]
                            
                            # Check if we have password for this email domain
                            if domain in self.config["user_data"]["email_passwords"]:
                                password = self.config["user_data"]["email_passwords"][domain]
                                
                                logging.info(f"Attempting to verify email: {email}")
                                verified = self.email_verifier.verify_email(email, password)
                                
                                if verified:
                                    logging.info(f"Successfully verified email: {email}")
                                    stats["verified"] += 1
                                else:
                                    logging.warning(f"Failed to verify email: {email}")
                            else:
                                logging.warning(f"No password available for email domain: {domain}")
                        
                        # Add account to results
                        account_info = {
                            "user_info": result,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "verified": verified,
                            "proxy": proxy
                        }
                        
                        stats["accounts"].append(account_info)
                        stats["success"] += 1
                        account_created = True
                    else:
                        logging.warning(f"Failed to create account: {result}")
                        retries += 1
                except Exception as e:
                    logging.error(f"Exception during account creation: {str(e)}")
                    retries += 1
                finally:
                    # Always close the creator
                    creator.close()
            
            if not account_created:
                stats["failed"] += 1
                logging.error(f"Failed to create account after {self.config['account_creation']['max_retries']} attempts")
            
            # Add delay between account creations
            if i < self.config["account_creation"]["num_accounts"] - 1:
                delay = random.randint(self.config["account_creation"]["min_delay"], self.config["account_creation"]["max_delay"])
                logging.info(f"Waiting {delay} seconds before next account creation")
                time.sleep(delay)
        
        # Save results
        stats["end_time"] = datetime.now()
        stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds() / 60.0
        
        self._save_results(stats)
        
        return stats
    
    def _save_results(self, stats):
        """Save account creation results to file
        
        Args:
            stats (dict): Statistics and account information
        """
        try:
            # Save to JSON file
            output_file = self.config["output"]["output_file"]
            with open(output_file, "w") as f:
                json.dump(stats, f, indent=4, default=str)
            
            # Also save to text file for easy reading
            txt_file = os.path.splitext(output_file)[0] + ".txt"
            with open(txt_file, "w") as f:
                f.write(f"Pinterest Account Creation Results\n")
                f.write(f"===============================\n\n")
                f.write(f"Start Time: {stats['start_time']}\n")
                f.write(f"End Time: {stats['end_time']}\n")
                f.write(f"Duration: {stats['duration']:.2f} minutes\n")
                f.write(f"Accounts Created: {stats['success']}\n")
                f.write(f"Failed Attempts: {stats['failed']}\n")
                f.write(f"Verified Accounts: {stats['verified']}\n\n")
                
                f.write(f"Account Details:\n")
                f.write(f"===============\n\n")
                
                for i, account in enumerate(stats["accounts"]):
                    f.write(f"Account {i+1}:\n")
                    f.write(f"  Email: {account['user_info']['email']}\n")
                    f.write(f"  Password: {account['user_info']['password']}\n")
                    f.write(f"  Username: {account['user_info']['username']}\n")
                    f.write(f"  Name: {account['user_info']['first_name']} {account['user_info']['last_name']}\n")
                    f.write(f"  Created: {account['created_at']}\n")
                    f.write(f"  Verified: {account['verified']}\n")
                    if account['proxy']:
                        f.write(f"  Proxy: {account['proxy']}\n")
                    f.write("\n")
            
            logging.info(f"Saved results to {output_file} and {txt_file}")
        except Exception as e:
            logging.error(f"Error saving results: {str(e)}")
    
    def _display_summary(self, stats):
        """Display summary of account creation process
        
        Args:
            stats (dict): Statistics from account creation
        """
        print("\n" + "=" * 50)
        print("PINTEREST ACCOUNT CREATION SUMMARY")
        print("=" * 50)
        print(f"Start Time: {stats['start_time']}")
        print(f"End Time: {stats['end_time']}")
        print(f"Duration: {stats['duration']:.2f} minutes")
        print(f"Accounts Created: {stats['success']}")
        print(f"Failed Attempts: {stats['failed']}")
        print(f"Verified Accounts: {stats['verified']}")
        
        if stats['success'] > 0:
            success_rate = (stats['success'] / (stats['success'] + stats['failed'])) * 100
            print(f"Success Rate: {success_rate:.2f}%")
            
            if stats['verified'] > 0:
                verification_rate = (stats['verified'] / stats['success']) * 100
                print(f"Verification Rate: {verification_rate:.2f}%")
        
        print("=" * 50)
        print(f"Created accounts saved to: {os.path.abspath(self.config['output']['output_file'])}")
        print("=" * 50)

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
    user_group.add_argument("--verify-email", action="store_true",
                           help="Enable email verification")
    
    # CAPTCHA options
    captcha_group = parser.add_argument_group("CAPTCHA Options")
    captcha_group.add_argument("--use-captcha-solver", action="store_true",
                              help="Use CAPTCHA solving service")
    captcha_group.add_argument("--captcha-api-key", type=str,
                              help="API key for CAPTCHA solving service")
    captcha_group.add_argument("--captcha-service", type=str, choices=["2captcha", "anticaptcha"],
                              help="CAPTCHA solving service to use")
    
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
    if args.verify_email:
        config["user_data"]["email_verification"] = True
    
    # Update CAPTCHA settings
    if args.use_captcha_solver:
        config["captcha"]["use_solver"] = True
    if args.captcha_api_key:
        config["captcha"]["api_key"] = args.captcha_api_key
    if args.captcha_service:
        config["captcha"]["service"] = args.captcha_service
    
    # Update output settings
    if args.output_file:
        config["output"]["output_file"] = args.output_file
    if args.log_level:
        config["output"]["log_level"] = args.log_level
        # Update logging level
        numeric_level = getattr(logging, args.log_level)
        logging.getLogger().setLevel(numeric_level)
    
    return config

def main():
    """Main function to run the Pinterest account creator"""
    try:
        # Parse command line arguments
        parser = setup_argument_parser()
        args = parser.parse_args()
        
        # Create Pinterest automation instance
        automation = PinterestAutomation(config_file=args.config)
        
        # Update configuration with command line arguments
        automation.config = update_config_from_args(automation.config, args)
        
        # Save updated configuration
        automation.save_config()
        
        # Run the automation
        automation.run()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()