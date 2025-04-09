import os
import time
import random
import string
import logging
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pinterest_creator.log"),
        logging.StreamHandler()
    ]
)

class PinterestAccountCreator:
    """A class to automate Pinterest account creation"""
    
    def __init__(self, headless=False, use_proxy=False, proxy=None):
        """Initialize the Pinterest account creator
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            use_proxy (bool): Whether to use a proxy
            proxy (str): Proxy address in format http://ip:port
        """
        self.headless = headless
        self.use_proxy = use_proxy
        self.proxy = proxy
        self.driver = None
        self.wait = None
        self.setup_driver()
        
    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Add user agent to appear more like a real user
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        if self.use_proxy and self.proxy:
            chrome_options.add_argument(f"--proxy-server={self.proxy}")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)  # 15 seconds timeout
            logging.info("WebDriver initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize WebDriver: {str(e)}")
            raise
    
    def generate_random_user(self):
        """Generate random user information for account creation
        
        Returns:
            dict: Dictionary containing user information
        """
        # First names list
        first_names = [
            "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
            "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
            "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
            "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
            "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
            "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa"
        ]
        
        # Last names list
        last_names = [
            "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
            "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
            "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee",
            "Walker", "Hall", "Allen", "Young", "Hernandez", "King", "Wright", "Lopez",
            "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter",
            "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans"
        ]
        
        # Generate random user information
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 9999)}"
        email_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
        email = f"{username}@{random.choice(email_domains)}"
        
        # Generate a strong password
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
    
    def save_account_info(self, user_info):
        """Save account information to a file
        
        Args:
            user_info (dict): User information to save
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        account_info = {
            "timestamp": timestamp,
            **user_info
        }
        
        # Save to JSON file
        try:
            if os.path.exists("pinterest_accounts.json"):
                with open("pinterest_accounts.json", "r") as f:
                    accounts = json.load(f)
            else:
                accounts = []
                
            accounts.append(account_info)
            
            with open("pinterest_accounts.json", "w") as f:
                json.dump(accounts, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save account info to JSON: {str(e)}")
        
        # Also save to text file for easy reading
        try:
            with open("pinterest_accounts.txt", "a") as f:
                f.write(f"\n--- Account Created: {timestamp} ---\n")
                f.write(f"Email: {user_info['email']}\n")
                f.write(f"Password: {user_info['password']}\n")
                f.write(f"Username: {user_info['username']}\n")
                f.write(f"Name: {user_info['first_name']} {user_info['last_name']}\n")
                f.write("----------------------------------------\n")
        except Exception as e:
            logging.error(f"Failed to save account info to text file: {str(e)}")
    
    def wait_for_element(self, by, value, timeout=15):
        """Wait for an element to be present and visible
        
        Args:
            by: The locator strategy
            value: The locator value
            timeout: Maximum time to wait in seconds
            
        Returns:
            The WebElement if found, None otherwise
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logging.warning(f"Timeout waiting for element: {by}={value}")
            return None
    
    def click_element(self, element, retry=3):
        """Safely click an element with retry logic
        
        Args:
            element: The WebElement to click
            retry: Number of retry attempts
            
        Returns:
            bool: True if click was successful, False otherwise
        """
        for attempt in range(retry):
            try:
                element.click()
                return True
            except ElementClickInterceptedException:
                logging.warning(f"Click intercepted, attempt {attempt+1} of {retry}")
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error clicking element: {str(e)}")
                time.sleep(1)
        return False
    
    def fill_signup_form(self, user_info):
        """Fill out the Pinterest signup form
        
        Args:
            user_info (dict): User information for signup
            
        Returns:
            bool: True if form was filled successfully, False otherwise
        """
        try:
            # Go to Pinterest signup page
            self.driver.get("https://www.pinterest.com/signup/")
            time.sleep(3)  # Allow page to load
            
            # Fill email field
            email_field = self.wait_for_element(By.ID, "email")
            if not email_field:
                return False
            email_field.send_keys(user_info["email"])
            
            # Fill password field
            password_field = self.wait_for_element(By.ID, "password")
            if not password_field:
                return False
            password_field.send_keys(user_info["password"])
            
            # Fill age field
            age_field = self.wait_for_element(By.ID, "age")
            if not age_field:
                return False
            age_field.send_keys(str(user_info["age"]))
            
            # Click continue button
            continue_button = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
            if not continue_button or not self.click_element(continue_button):
                return False
            
            time.sleep(2)  # Wait for next page
            
            # Fill name fields if they appear
            first_name_field = self.wait_for_element(By.ID, "first_name", timeout=5)
            if first_name_field:
                first_name_field.send_keys(user_info["first_name"])
                
                last_name_field = self.wait_for_element(By.ID, "last_name")
                if last_name_field:
                    last_name_field.send_keys(user_info["last_name"])
                
                # Click continue again
                continue_button = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
                if not continue_button or not self.click_element(continue_button):
                    return False
            
            logging.info("Signup form filled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error filling signup form: {str(e)}")
            return False
    
    def select_interests(self):
        """Select random interests during the signup process
        
        Returns:
            bool: True if interests were selected successfully, False otherwise
        """
        try:
            # Wait for interests page to load
            time.sleep(3)
            
            # Check if we're on the interests selection page
            interest_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='interest-card']")
            if not interest_elements:
                logging.info("No interest selection page found, may have been skipped")
                return True
            
            # Select 5-10 random interests
            num_interests = min(len(interest_elements), random.randint(5, 10))
            selected_interests = random.sample(interest_elements, num_interests)
            
            for interest in selected_interests:
                try:
                    self.click_element(interest)
                    time.sleep(0.5)  # Small delay between selections
                except Exception:
                    continue  # Skip if can't click this interest
            
            # Click next/done button
            next_button = self.wait_for_element(By.CSS_SELECTOR, "button[data-test-id='next-btn']")
            if next_button:
                self.click_element(next_button)
            else:
                done_button = self.wait_for_element(By.CSS_SELECTOR, "button[data-test-id='done-btn']")
                if done_button:
                    self.click_element(done_button)
            
            logging.info("Interests selected successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error selecting interests: {str(e)}")
            return False
    
    def handle_verification(self):
        """Handle any verification steps that may appear
        
        Returns:
            bool: True if verification was handled or not needed, False otherwise
        """
        try:
            # Check for CAPTCHA or verification elements
            # This is a placeholder - actual implementation would depend on Pinterest's verification methods
            verification_element = self.wait_for_element(By.CSS_SELECTOR, "[data-test-id='verification-code-input']", timeout=5)
            
            if verification_element:
                logging.warning("Verification required - manual intervention needed")
                # If running in headless mode, we can't handle verification
                if self.headless:
                    return False
                
                # Wait for manual verification (up to 2 minutes)
                for _ in range(120):
                    # Check if we've moved past verification
                    if "pinterest.com/homefeed" in self.driver.current_url:
                        logging.info("Verification completed successfully")
                        return True
                    time.sleep(1)
                
                return False
            
            # No verification needed
            return True
            
        except Exception as e:
            logging.error(f"Error handling verification: {str(e)}")
            return False
    
    def check_account_created(self):
        """Check if account was created successfully
        
        Returns:
            bool: True if account was created successfully, False otherwise
        """
        try:
            # Wait for redirect to home feed or profile page
            time.sleep(5)
            
            # Check if we're on a Pinterest page that indicates successful login
            success_indicators = [
                "pinterest.com/homefeed",
                "pinterest.com/settings",
                "pinterest.com/following",
                "pinterest.com/"
            ]
            
            current_url = self.driver.current_url
            for indicator in success_indicators:
                if indicator in current_url:
                    logging.info(f"Account created successfully, redirected to: {current_url}")
                    return True
            
            logging.warning(f"Unexpected redirect after signup: {current_url}")
            return False
            
        except Exception as e:
            logging.error(f"Error checking account creation: {str(e)}")
            return False
    
    def create_account(self, user_info=None):
        """Create a Pinterest account
        
        Args:
            user_info (dict, optional): User information for signup. If None, random info will be generated.
            
        Returns:
            tuple: (success, result) where success is a boolean indicating if account creation was successful,
                  and result is either the user_info dict if successful or an error message if failed
        """
        if not user_info:
            user_info = self.generate_random_user()
        
        logging.info(f"Starting account creation for {user_info['email']}")
        
        try:
            # Step 1: Fill signup form
            if not self.fill_signup_form(user_info):
                return False, "Failed to fill signup form"
            
            # Step 2: Select interests
            if not self.select_interests():
                return False, "Failed to select interests"
            
            # Step 3: Handle verification if needed
            if not self.handle_verification():
                return False, "Failed to complete verification"
            
            # Step 4: Check if account was created successfully
            if not self.check_account_created():
                return False, "Failed to confirm account creation"
            
            # Save account information
            self.save_account_info(user_info)
            
            logging.info(f"Account created successfully for {user_info['email']}")
            return True, user_info
            
        except Exception as e:
            error_msg = f"Error creating account: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logging.info("WebDriver closed")

def main():
    """Main function to demonstrate usage"""
    try:
        # Create an instance of PinterestAccountCreator
        creator = PinterestAccountCreator(headless=False)  # Set to True for headless mode
        
        # Create a Pinterest account
        success, result = creator.create_account()
        
        if success:
            print(f"Account created successfully!")
            print(f"Email: {result['email']}")
            print(f"Password: {result['password']}")
        else:
            print(f"Failed to create account: {result}")
        
        # Close the WebDriver
        creator.close()
        
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    main()