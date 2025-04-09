import os
import time
import random
import json
import logging
import argparse
from datetime import datetime
from pinterest_account_creator import PinterestAccountCreator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_creator.log"),
        logging.StreamHandler()
    ]
)

class UserGenerator:
    """A class to generate random user information"""
    
    def __init__(self, data_file=None):
        """Initialize the user generator
        
        Args:
            data_file (str, optional): Path to a JSON file with custom user data
        """
        self.data_file = data_file
        self.custom_data = None
        
        if data_file and os.path.exists(data_file):
            try:
                with open(data_file, 'r') as f:
                    self.custom_data = json.load(f)
                logging.info(f"Loaded custom user data from {data_file}")
            except Exception as e:
                logging.error(f"Failed to load custom user data: {str(e)}")
    
    def generate_user(self):
        """Generate random user information
        
        Returns:
            dict: Dictionary containing user information
        """
        # If we have custom data, use it to generate a user
        if self.custom_data:
            return self._generate_from_custom_data()
        
        # Otherwise, use the built-in generator from PinterestAccountCreator
        creator = PinterestAccountCreator(headless=True)
        user_info = creator.generate_random_user()
        creator.close()
        return user_info
    
    def _generate_from_custom_data(self):
        """Generate user information from custom data
        
        Returns:
            dict: Dictionary containing user information
        """
        # This is a simplified implementation - in a real scenario,
        # you would have more sophisticated logic to combine elements
        # from your custom data
        
        first_names = self.custom_data.get("first_names", [])
        last_names = self.custom_data.get("last_names", [])
        domains = self.custom_data.get("email_domains", ["gmail.com", "yahoo.com", "outlook.com"])
        
        if not first_names or not last_names:
            # Fall back to built-in generator if custom data is incomplete
            creator = PinterestAccountCreator(headless=True)
            user_info = creator.generate_random_user()
            creator.close()
            return user_info
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 9999)}"
        email = f"{username}@{random.choice(domains)}"
        
        # Generate a strong password
        import string
        password_length = random.randint(12, 16)
        password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(password_chars) for _ in range(password_length))
        
        # Generate random age between 18 and 65
        age = random.randint(18, 65)
        
        # Generate random gender
        gender = random.choice(["male", "female"])
        
        user_info = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "password": password,
            "age": age,
            "gender": gender
        }
        
        return user_info

class ProxyHandler:
    """A class to handle proxy rotation for account creation"""
    
    def __init__(self, proxy_file=None, proxy_list=None, proxy_api_url=None, proxy_api_key=None):
        """Initialize the proxy handler
        
        Args:
            proxy_file (str, optional): Path to a file containing proxies (one per line)
            proxy_list (list, optional): List of proxy strings
            proxy_api_url (str, optional): URL for a proxy API service
            proxy_api_key (str, optional): API key for the proxy service
        """
        self.proxies = []
        self.current_index = 0
        self.proxy_api_url = proxy_api_url
        self.proxy_api_key = proxy_api_key
        
        # Load proxies from file if provided
        if proxy_file and os.path.exists(proxy_file):
            try:
                with open(proxy_file, 'r') as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                logging.info(f"Loaded {len(self.proxies)} proxies from {proxy_file}")
            except Exception as e:
                logging.error(f"Failed to load proxies from file: {str(e)}")
        
        # Add proxies from list if provided
        if proxy_list:
            self.proxies.extend(proxy_list)
            logging.info(f"Added {len(proxy_list)} proxies from list")
        
        # Fetch proxies from API if provided
        if proxy_api_url and proxy_api_key:
            self._fetch_proxies_from_api()
    
    def _fetch_proxies_from_api(self):
        """Fetch proxies from the API service"""
        try:
            import requests
            headers = {"Authorization": f"Bearer {self.proxy_api_key}"}
            response = requests.get(self.proxy_api_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "proxies" in data:
                    self.proxies.extend(data["proxies"])
                    logging.info(f"Fetched {len(data['proxies'])} proxies from API")
                else:
                    logging.warning("API response did not contain proxies")
            else:
                logging.error(f"Failed to fetch proxies from API: {response.status_code}")
        except Exception as e:
            logging.error(f"Error fetching proxies from API: {str(e)}")
    
    def get_random_proxy(self):
        """Get a random proxy from the list
        
        Returns:
            str: A proxy string or None if no proxies are available
        """
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def get_next_proxy(self):
        """Get the next proxy in the rotation
        
        Returns:
            str: A proxy string or None if no proxies are available
        """
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

class BatchAccountCreator:
    """A class to create multiple Pinterest accounts in batch mode"""
    
    def __init__(self, config=None):
        """Initialize the batch account creator
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        # Default configuration
        self.config = {
            "num_accounts": 1,
            "headless": False,
            "use_proxy": False,
            "proxy_file": None,
            "proxy_list": None,
            "proxy_api_url": None,
            "proxy_api_key": None,
            "user_data_file": None,
            "output_file": "pinterest_accounts.json",
            "min_delay": 30,
            "max_delay": 120,
            "max_retries": 3,
            "verify_success": True
        }
        
        # Update with provided configuration
        if config:
            self.config.update(config)
        
        # Initialize components
        self.user_generator = UserGenerator(data_file=self.config["user_data_file"])
        
        # Initialize proxy handler if using proxies
        self.proxy_handler = None
        if self.config["use_proxy"]:
            self.proxy_handler = ProxyHandler(
                proxy_file=self.config["proxy_file"],
                proxy_list=self.config["proxy_list"],
                proxy_api_url=self.config["proxy_api_url"],
                proxy_api_key=self.config["proxy_api_key"]
            )
        
        # Statistics
        self.stats = {
            "total": self.config["num_accounts"],
            "success": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None
        }
    
    def create_accounts(self):
        """Create multiple Pinterest accounts according to configuration
        
        Returns:
            dict: Statistics about the account creation process
        """
        self.stats["start_time"] = datetime.now()
        logging.info(f"Starting batch creation of {self.config['num_accounts']} Pinterest accounts")
        
        successful_accounts = []
        failed_attempts = []
        
        for i in range(self.config["num_accounts"]):
            logging.info(f"Creating account {i+1} of {self.config['num_accounts']}")
            
            # Get proxy if using proxies
            proxy = None
            if self.config["use_proxy"] and self.proxy_handler:
                proxy = self.proxy_handler.get_random_proxy()
                if not proxy:
                    logging.warning("No proxy available, continuing without proxy")
            
            # Create account with retries
            account_created = False
            retries = 0
            
            while not account_created and retries < self.config["max_retries"]:
                if retries > 0:
                    logging.info(f"Retry attempt {retries} for account {i+1}")
                    
                    # Get a new proxy for retry if available
                    if self.config["use_proxy"] and self.proxy_handler:
                        proxy = self.proxy_handler.get_next_proxy()
                
                # Generate user info
                user_info = self.user_generator.generate_user()
                
                # Create Pinterest account creator instance
                creator = PinterestAccountCreator(
                    headless=self.config["headless"],
                    use_proxy=self.config["use_proxy"],
                    proxy=proxy
                )
                
                try:
                    # Create account
                    success, result = creator.create_account(user_info=user_info)
                    
                    if success:
                        logging.info(f"Successfully created account: {result['email']}")
                        successful_accounts.append(result)
                        account_created = True
                        self.stats["success"] += 1
                    else:
                        logging.warning(f"Failed to create account: {result}")
                        failed_attempts.append({
                            "user_info": user_info,
                            "error": result,
                            "attempt": retries + 1
                        })
                        retries += 1
                except Exception as e:
                    logging.error(f"Exception during account creation: {str(e)}")
                    failed_attempts.append({
                        "user_info": user_info,
                        "error": str(e),
                        "attempt": retries + 1
                    })
                    retries += 1
                finally:
                    # Always close the creator
                    creator.close()
            
            if not account_created:
                self.stats["failed"] += 1
                logging.error(f"Failed to create account after {self.config['max_retries']} attempts")
            
            # Add delay between account creations
            if i < self.config["num_accounts"] - 1:
                delay = random.randint(self.config["min_delay"], self.config["max_delay"])
                logging.info(f"Waiting {delay} seconds before next account creation")
                time.sleep(delay)
        
        # Save results
        self.stats["end_time"] = datetime.now()
        self.stats["duration"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds() / 60.0
        
        self._save_results(successful_accounts, failed_attempts)
        
        return self.stats
    
    def _save_results(self, successful_accounts, failed_attempts):
        """Save the results of the batch account creation
        
        Args:
            successful_accounts (list): List of successfully created accounts
            failed_attempts (list): List of failed account creation attempts
        """
        results = {
            "stats": self.stats,
            "successful_accounts": successful_accounts,
            "failed_attempts": failed_attempts
        }
        
        # Convert datetime objects to strings for JSON serialization
        results["stats"]["start_time"] = results["stats"]["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        results["stats"]["end_time"] = results["stats"]["end_time"].strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open(self.config["output_file"], "w") as f:
                json.dump(results, f, indent=4)
            logging.info(f"Results saved to {self.config['output_file']}")
        except Exception as e:
            logging.error(f"Failed to save results: {str(e)}")

def parse_arguments():
    """Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Batch Pinterest Account Creator")
    
    parser.add_argument("-n", "--num-accounts", type=int, default=1,
                        help="Number of accounts to create (default: 1)")
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode (no visible browser)")
    parser.add_argument("--use-proxy", action="store_true",
                        help="Use proxies for account creation")
    parser.add_argument("--proxy-file", type=str,
                        help="Path to file containing proxies (one per line)")
    parser.add_argument("--user-data-file", type=str,
                        help="Path to JSON file with custom user data")
    parser.add_argument("--output-file", type=str, default="pinterest_accounts.json",
                        help="Path to output file (default: pinterest_accounts.json)")
    parser.add_argument("--min-delay", type=int, default=30,
                        help="Minimum delay between account creations in seconds (default: 30)")
    parser.add_argument("--max-delay", type=int, default=120,
                        help="Maximum delay between account creations in seconds (default: 120)")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Maximum retry attempts per account (default: 3)")
    
    return parser.parse_args()

def main():
    """Main function to run the batch account creator"""
    args = parse_arguments()
    
    # Create configuration from arguments
    config = {
        "num_accounts": args.num_accounts,
        "headless": args.headless,
        "use_proxy": args.use_proxy,
        "proxy_file": args.proxy_file,
        "user_data_file": args.user_data_file,
        "output_file": args.output_file,
        "min_delay": args.min_delay,
        "max_delay": args.max_delay,
        "max_retries": args.max_retries
    }
    
    # Create batch account creator
    creator = BatchAccountCreator(config)
    
    # Create accounts
    stats = creator.create_accounts()
    
    # Print summary
    print("\nBatch Account Creation Summary:")
    print(f"Total accounts: {stats['total']}")
    print(f"Successful: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Duration: {stats['duration']:.2f} minutes")
    print(f"Results saved to: {config['output_file']}")

if __name__ == "__main__":
    main()