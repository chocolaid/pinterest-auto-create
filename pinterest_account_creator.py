import os
import sys
import json
import time
import random
import string
import logging
import requests
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import undetected_chromedriver as uc
from email_verification import EmailVerifier

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
    
    def __init__(self, headless=False, use_proxy=False, proxy=None, use_temp_mail=True):
        """Initialize the Pinterest account creator
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            use_proxy (bool): Whether to use a proxy
            proxy (str): Proxy address in format http://ip:port
            use_temp_mail (bool): Whether to use temp mail for email verification
        """
        self.headless = headless
        self.use_proxy = use_proxy
        self.proxy = proxy
        self.use_temp_mail = use_temp_mail
        self.driver = None
        self.wait = None
        self.email_verifier = None
        self.setup_driver()
        
    def setup_driver(self):
        """Set up Selenium WebDriver using undetected_chromedriver"""
        try:
            # Configure Chrome options
            options = uc.ChromeOptions()
            
            # Add headless option if specified
            if self.headless:
                options.add_argument("--headless=new")
            
            # Add proxy if specified
            if self.use_proxy and self.proxy:
                options.add_argument(f'--proxy-server={self.proxy}')
            
            # Add standard options for performance and stability
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Add experimental options to avoid detection
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize undetected_chromedriver with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Try to initialize with specific version
                    self.driver = uc.Chrome(
                        options=options,
                        headless=self.headless,
                        use_subprocess=True,
                        driver_executable_path=None,  # Let undetected_chromedriver handle the path
                        version_main=None  # Let it auto-detect the version
                    )
                    
                    # Set window size
                    self.driver.set_window_size(1366, 768)
                    
                    # Set up WebDriverWait
                    self.wait = WebDriverWait(self.driver, 15)
                    
                    # Execute CDP commands to avoid detection
                    self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    })
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    
                    logging.info("WebDriver initialized successfully")
                    return True
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(f"Failed to initialize WebDriver after {max_retries} attempts: {str(e)}")
                        # Try to clean up any remaining files
                        try:
                            import shutil
                            import os
                            appdata = os.getenv('APPDATA')
                            if appdata:
                                undetected_path = os.path.join(appdata, 'undetected_chromedriver')
                                if os.path.exists(undetected_path):
                                    shutil.rmtree(undetected_path)
                        except Exception as cleanup_error:
                            logging.error(f"Failed to clean up undetected_chromedriver files: {str(cleanup_error)}")
                        return False
                    logging.warning(f"Retrying WebDriver initialization (attempt {attempt + 1}/{max_retries})")
                    time.sleep(5)
            
        except Exception as e:
            logging.error(f"Error in setup_driver: {str(e)}")
            return False
    
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
        
        # Generate a strong password
        password_length = random.randint(12, 16)
        password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(password_chars) for _ in range(password_length))
        
        # Generate random gender
        gender = random.choice(["male", "female"])
        
        user_info = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "password": password,
            "gender": gender
        }
        
        # If using temp mail, we'll get the email address later
        if not self.use_temp_mail:
            email_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
            email = f"{username}@{random.choice(email_domains)}"
            user_info["email"] = email
        
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
            # Go to Pinterest signup page with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver.get("https://www.pinterest.com/signup/")
                    # Wait for page to load
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='signup-form']"))
                    )
                    break
                except TimeoutException:
                    if attempt == max_retries - 1:
                        logging.error("Failed to load signup page after multiple attempts")
                        return False
                    logging.warning(f"Retrying to load signup page (attempt {attempt + 1}/{max_retries})")
                    time.sleep(5)
            
            # Wait for signup button and click it
            try:
                signup_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.RCK.Hsu.USg.adn.NTm.KhY.iyn.S9z.F10.xD4.i1W.V92.a_A.hNT.BG7.hDj._O1.KS5.mQ8.Tbt.L4E div.X8m.tg7.tBJ.dyH.iFc.sAJ.H2s"))
                )
                self.click_element(signup_button)
            except TimeoutException:
                logging.error("Signup button not found or not clickable")
                return False
            
            # Fill email field
            try:
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                email_field.clear()
                email_field.send_keys(user_info["email"])
            except TimeoutException:
                logging.error("Email field not found")
                return False
            
            # Fill password field
            try:
                password_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
                password_field.clear()
                password_field.send_keys(user_info["password"])
            except TimeoutException:
                logging.error("Password field not found")
                return False
            
            # Wait for birthdate field to be present
            try:
                birthdate_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "birthdate"))
                )
            except TimeoutException:
                logging.error("Birthdate field not found")
                return False
            
            # Set birthdate using JavaScript that simulates real user input
            js_code = """
            // Find the input
            const birthdayInput = document.getElementById('birthdate');
            
            // Generate a random birthday between 18 and 90 years old
            function randomBirthday() {
              const today = new Date();
              const minAge = 18;
              const maxAge = 90;
              
              const startYear = today.getFullYear() - maxAge;
              const endYear = today.getFullYear() - minAge;
              
              const randomYear = Math.floor(Math.random() * (endYear - startYear + 1)) + startYear;
              const randomMonth = Math.floor(Math.random() * 12); // 0-11
              const randomDay = Math.floor(Math.random() * 28) + 1; // To avoid invalid dates like Feb 30
            
              const randomDate = new Date(randomYear, randomMonth, randomDay);
              
              // Format to yyyy-mm-dd
              const yyyy = randomDate.getFullYear();
              const mm = String(randomDate.getMonth() + 1).padStart(2, '0');
              const dd = String(randomDate.getDate()).padStart(2, '0');
            
              return `${yyyy}-${mm}-${dd}`;
            }
            
            // Set the value and simulate real user input
            function simulateUserTypingBirthday(inputElement, value) {
              const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
              nativeInputValueSetter.call(inputElement, value);
            
              // Dispatch input and change events to simulate user action
              inputElement.dispatchEvent(new Event('input', { bubbles: true }));
              inputElement.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            // Main logic
            if (birthdayInput) {
              const birthday = randomBirthday();
              simulateUserTypingBirthday(birthdayInput, birthday);
            } else {
              console.error('Birthday input not found!');
            }
            """
            
            # Execute the JavaScript code
            self.driver.execute_script(js_code)
            
            # Small delay to ensure the value is set
            time.sleep(0.5)
            
            # Click continue button
            try:
                continue_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
                )
                self.click_element(continue_button)
            except TimeoutException:
                logging.error("Continue button not found or not clickable")
                return False
            
            time.sleep(2)  # Wait for next page
            
            # Fill name fields if they appear
            try:
                first_name_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "first_name"))
                )
                first_name_field.clear()
                first_name_field.send_keys(user_info["first_name"])
                
                last_name_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "last_name"))
                )
                last_name_field.clear()
                last_name_field.send_keys(user_info["last_name"])
                
                # Click continue again
                continue_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
                )
                self.click_element(continue_button)
            except TimeoutException:
                logging.warning("Name fields not found, may have been skipped")
            
            logging.info("Signup form filled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error filling signup form: {str(e)}")
            return False


    def select_gender(self):
        """Select gender during the signup process"""
        try:
            # Wait for gender selection page to load
            time.sleep(3)
            
            # Find only male and female gender options
            gender_options = []
            female_option = self.driver.find_element(By.CSS_SELECTOR, "div[data-test-id='nux-gender-female-label']")
            male_option = self.driver.find_element(By.CSS_SELECTOR, "div[data-test-id='nux-gender-male-label']")
            
            if female_option:
                gender_options.append(female_option)
            if male_option:
                gender_options.append(male_option)
            
            if not gender_options:
                logging.error("No gender options found")
                return False
            
            # Select a random gender option (only between male and female)
            selected_gender = random.choice(gender_options)
            
            # Find the radio input within the selected gender option
            radio_input = selected_gender.find_element(By.CSS_SELECTOR, "input[type='radio']")
            if not radio_input:
                logging.error("Could not find radio input for selected gender")
                return False
            
            # Click the radio input
            self.click_element(radio_input)
            
            # Get the gender value for logging
            gender_value = radio_input.get_attribute("value")
            logging.info(f"Selected gender: {gender_value}")
            
            # Click next button to proceed
            time.sleep(3)
            next_button = self.wait_for_element(By.CSS_SELECTOR, "button[data-test-id='nux-locale-country-next-btn']")
            if next_button:
                self.click_element(next_button)
            else:
                logging.warning("Next button not found after gender selection")
            
            return True
            
        except Exception as e:
            logging.error(f"Error selecting gender: {str(e)}")
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
            interest_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='nux-picker-topic']")
            if not interest_elements:
                logging.info("No interest selection page found, may have been skipped")
                return True
            
            # Select 5-10 random interests
            num_interests = min(len(interest_elements), random.randint(5, 10))
            selected_interests = random.sample(interest_elements, num_interests)
            
            for interest in selected_interests:
                try:
                    # Find the clickable button within the interest element
                    button = interest.find_element(By.CSS_SELECTOR, "div[role='button']")
                    self.click_element(button)
                    time.sleep(0.5)  # Small delay between selections
                except Exception:
                    continue  # Skip if can't click this interest
            
            # Try to find and click the next/done/home feed button
            next_button = self.wait_for_element(By.CSS_SELECTOR, "button[data-test-id='next-btn']")
            if next_button:
                self.click_element(next_button)
            else:
                done_button = self.wait_for_element(By.CSS_SELECTOR, "button[data-test-id='done-btn']")
                if done_button:
                    self.click_element(done_button)
                else:
                    # Look for "Meet your home feed" button
                    home_feed_button = self.wait_for_element(By.XPATH, "//button[.//div[contains(text(), 'Meet your home feed')]]")
                    if home_feed_button:
                        self.click_element(home_feed_button)
            
            logging.info("Interests selected successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error selecting interests: {str(e)}")
            return False
    
    def handle_verification(self, email=None):
        """Handle email verification for Pinterest account
        
        Args:
            email (str, optional): Email to verify (for temp mail, this is None)
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        try:
            # Initialize email verifier if not already done
            if not self.email_verifier:
                self.email_verifier = EmailVerifier(headless=self.headless, use_existing_driver=True, driver=self.driver)
            
            # If using temp mail, verify with that
            if self.use_temp_mail and hasattr(self.email_verifier, 'temp_mail') and self.email_verifier.temp_mail:
                logging.info("Verifying email with temp mail")
                return self.email_verifier.verify_with_temp_mail(timeout=600, check_interval=60)
            
            # Otherwise, this method serves as a placeholder for manual verification
            # as we don't have passwords for regular email accounts
            logging.warning("Email verification required but no method available")
            logging.warning("Check your email and verify the account manually")
            
            # Wait for manual verification (up to 2 minutes)
            for _ in range(120):
                # Check if we've moved past verification
                if "pinterest.com/homefeed" in self.driver.current_url:
                    logging.info("Verification completed successfully")
                    return True
                time.sleep(1)
            
            return False
            
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
    
    def create_account(self, user_info=None, max_retries=3):
        """Create a Pinterest account with retry mechanism
        
        Args:
            user_info (dict, optional): User information for signup. If None, random info will be generated.
            max_retries (int): Maximum number of retry attempts for the entire process
            
        Returns:
            tuple: (success, result) where success is a boolean indicating if account creation was successful,
                  and result is either the user_info dict if successful or an error message if failed
        """
        if not user_info:
            user_info = self.generate_random_user()
        
        for attempt in range(max_retries):
            try:
                # If using temp mail, generate email address
                if self.use_temp_mail:
                    # Create email verifier if not already done
                    if not self.email_verifier:
                        self.email_verifier = EmailVerifier(headless=self.headless, use_existing_driver=True, driver=self.driver)
                    
                    # Generate temp email
                    email = self.email_verifier.generate_temp_mail()
                    user_info['email'] = email
                    logging.info(f"Generated temporary email: {email}")
                
                logging.info(f"Starting account creation for {user_info['email']} (attempt {attempt + 1}/{max_retries})")
                
                # Step 1: Fill signup form
                if not self.fill_signup_form(user_info):
                    logging.warning(f"Failed to fill signup form (attempt {attempt + 1}/{max_retries})")
                    continue

                #click next to show gender field
                time.sleep(3)
                next_button = self.wait_for_element(By.CSS_SELECTOR, "button[aria-label='Next']")
                if not next_button or not self.click_element(next_button):
                    logging.warning(f"Failed to click next button (attempt {attempt + 1}/{max_retries})")
                    continue

                #select gender
                if not self.select_gender():
                    logging.warning(f"Failed to select gender (attempt {attempt + 1}/{max_retries})")
                    continue

                #click next to accept prefield location and submit
                time.sleep(3)
                next_button = self.wait_for_element(By.CSS_SELECTOR, "button[data-test-id='nux-locale-country-next-btn']")
                if not next_button or not self.click_element(next_button):
                    logging.warning(f"Failed to click next button for prefield location (attempt {attempt + 1}/{max_retries})")
                    continue
                
                # Step 2: Select interests
                if not self.select_interests():
                    logging.warning(f"Failed to select interests (attempt {attempt + 1}/{max_retries})")
                    continue
                
                # Step 3: Check if account was created successfully
                if not self.check_account_created():
                    logging.warning(f"Failed to confirm account creation (attempt {attempt + 1}/{max_retries})")
                    continue
                
                logging.info(f"Account created successfully for {user_info['email']}")
                return True, user_info
                
            except Exception as e:
                error_msg = f"Error creating account (attempt {attempt + 1}/{max_retries}): {str(e)}"
                logging.error(error_msg)
                
                if attempt < max_retries - 1:
                    logging.info(f"Retrying account creation in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
                return False, error_msg
            finally:
                # Only close email verifier if we're not retrying
                if attempt == max_retries - 1 and self.email_verifier:
                    self.email_verifier.close()
                    self.email_verifier = None
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logging.info("WebDriver closed")
        # Don't close the email_verifier separately since it's using the same driver
        self.email_verifier = None
            
    def quit(self):
        """Alias for close method"""
        self.close()

def main():
    """Main function to demonstrate usage"""
    try:
        # Create an instance of PinterestAccountCreator with temp mail
        creator = PinterestAccountCreator(headless=False, use_temp_mail=True)
        
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