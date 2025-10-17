import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional
from pinterest_account_creator import PinterestAccountCreator
from email_verification import EmailVerifier
import json
from datetime import datetime

class AccountManager:
    """Manages multi-threaded account creation and verification"""
    
    def __init__(self, 
                 num_creation_threads: int = 2,
                 num_verification_threads: int = 3,
                 headless: bool = False,
                 use_proxy: bool = False,
                 proxy: Optional[str] = None,
                 use_temp_mail: bool = True):
        """Initialize the account manager
        
        Args:
            num_creation_threads: Number of threads for account creation
            num_verification_threads: Number of threads for email verification
            headless: Whether to run browsers in headless mode
            use_proxy: Whether to use proxies
            proxy: Proxy address if use_proxy is True
            use_temp_mail: Whether to use temp mail for verification
        """
        self.num_creation_threads = num_creation_threads
        self.num_verification_threads = num_verification_threads
        self.headless = headless
        self.use_proxy = use_proxy
        self.proxy = proxy
        self.use_temp_mail = use_temp_mail
        
        # Thread pools
        self.creation_pool = ThreadPoolExecutor(max_workers=num_creation_threads)
        self.verification_pool = ThreadPoolExecutor(max_workers=num_verification_threads)
        
        # Queues
        self.verification_queue = queue.Queue()
        self.completed_accounts = queue.Queue()
        
        # Locks
        self.log_lock = threading.Lock()
        self.file_lock = threading.Lock()
        
        # Track active creators and verifiers
        self.active_creators: Dict[int, PinterestAccountCreator] = {}
        self.active_verifiers: Dict[int, EmailVerifier] = {}
        
        # Control flags
        self.is_running = True
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
            handlers=[
                logging.FileHandler("pinterest_creator.log"),
                logging.StreamHandler()
            ]
        )
    
    def create_account(self, creator_id: int):
        """Create a Pinterest account in a separate thread
        
        Args:
            creator_id: Unique ID for this creator instance
        """
        try:
            # Create a new account creator
            creator = PinterestAccountCreator(
                headless=self.headless,
                use_proxy=self.use_proxy,
                proxy=self.proxy,
                use_temp_mail=self.use_temp_mail
            )
            
            # Store the creator
            self.active_creators[creator_id] = creator
            
            # Create account
            success, result = creator.create_account()
            
            if success:
                # Add to verification queue
                self.verification_queue.put((creator_id, result))
                with self.log_lock:
                    logging.info(f"Account created successfully: {result['email']}")
            else:
                with self.log_lock:
                    logging.error(f"Failed to create account: {result}")
            
        except Exception as e:
            with self.log_lock:
                logging.error(f"Error in account creation thread {creator_id}: {str(e)}")
        finally:
            # Clean up
            if creator_id in self.active_creators:
                self.active_creators[creator_id].close()
                del self.active_creators[creator_id]
    
    def verify_account(self, verifier_id: int):
        """Verify a Pinterest account in a separate thread
        
        Args:
            verifier_id: Unique ID for this verifier instance
        """
        while self.is_running:
            try:
                # Get next account to verify
                creator_id, account_info = self.verification_queue.get(timeout=5)
                
                # Create verifier if needed
                if verifier_id not in self.active_verifiers:
                    verifier = EmailVerifier(
                        headless=self.headless,
                        use_existing_driver=False
                    )
                    self.active_verifiers[verifier_id] = verifier
                
                verifier = self.active_verifiers[verifier_id]
                
                # Verify account
                success = verifier.verify_with_temp_mail(timeout=600, check_interval=60)
                
                if success:
                    # Save verified account
                    with self.file_lock:
                        self.save_verified_account(account_info)
                    with self.log_lock:
                        logging.info(f"Account verified successfully: {account_info['email']}")
                else:
                    with self.log_lock:
                        logging.error(f"Failed to verify account: {account_info['email']}")
                
            except queue.Empty:
                # No accounts to verify, continue waiting
                continue
            except Exception as e:
                with self.log_lock:
                    logging.error(f"Error in verification thread {verifier_id}: {str(e)}")
    
    def save_verified_account(self, account_info: dict):
        """Save verified account information
        
        Args:
            account_info: Dictionary containing account information
        """
        try:
            # Save to JSON file
            with open("pinterest_accounts.json", "a") as f:
                json.dump(account_info, f)
                f.write("\n")
            
            # Save to text file
            with open("pinterest_accounts.txt", "a") as f:
                f.write(f"\n--- Account Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                f.write(f"Email: {account_info['email']}\n")
                f.write(f"Password: {account_info['password']}\n")
                f.write(f"Username: {account_info['username']}\n")
                f.write(f"Name: {account_info['first_name']} {account_info['last_name']}\n")
                f.write("----------------------------------------\n")
                
        except Exception as e:
            logging.error(f"Error saving account info: {str(e)}")
    
    def start(self):
        """Start the account creation and verification process"""
        try:
            # Start creation threads
            for i in range(self.num_creation_threads):
                self.creation_pool.submit(self.create_account, i)
            
            # Start verification threads
            for i in range(self.num_verification_threads):
                self.verification_pool.submit(self.verify_account, i)
            
            # Wait for all threads to complete
            self.creation_pool.shutdown(wait=True)
            self.verification_pool.shutdown(wait=True)
            
        except KeyboardInterrupt:
            with self.log_lock:
                logging.info("Shutting down gracefully...")
            self.is_running = False
            self.creation_pool.shutdown(wait=False)
            self.verification_pool.shutdown(wait=False)
        finally:
            # Clean up all creators and verifiers
            for creator in self.active_creators.values():
                creator.close()
            for verifier in self.active_verifiers.values():
                verifier.close()
    
    def stop(self):
        """Stop the account creation and verification process"""
        self.is_running = False
        self.creation_pool.shutdown(wait=False)
        self.verification_pool.shutdown(wait=False) 