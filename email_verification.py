import time
import logging
import imaplib
import email
import re
import random
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("email_verification.log"),
        logging.StreamHandler()
    ]
)

class EmailVerifier:
    """A class to handle email verification for Pinterest accounts"""
    
    def __init__(self, headless=True):
        """Initialize the email verifier
        
        Args:
            headless (bool): Whether to run the browser in headless mode
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        
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
        chrome_options.add_argument("--window-size=1366,768")
        
        # Add user agent to appear more like a real user
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)  # 15 seconds timeout
            logging.info("WebDriver initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize WebDriver: {str(e)}")
            raise
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logging.info("WebDriver closed")
    
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
    
    def verify_gmail_account(self, email, password, max_attempts=5, delay=60):
        """Verify Pinterest account using Gmail
        
        Args:
            email (str): Gmail email address
            password (str): Gmail password
            max_attempts (int): Maximum number of attempts to check for verification email
            delay (int): Delay between attempts in seconds
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        try:
            # Connect to Gmail IMAP server
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(email, password)
            mail.select('inbox')
            
            # Search for Pinterest verification emails
            verification_link = None
            attempts = 0
            
            while not verification_link and attempts < max_attempts:
                logging.info(f"Checking for verification email (attempt {attempts+1}/{max_attempts})")
                
                # Search for emails from Pinterest
                status, messages = mail.search(None, '(FROM "pinterest@account.pinterest.com" SUBJECT "Verify your email")')
                
                if status == 'OK' and messages[0]:
                    # Get the latest email
                    latest_email_id = messages[0].split()[-1]
                    status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
                    
                    if status == 'OK':
                        # Parse email content
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        # Extract verification link
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == 'text/html':
                                    body = part.get_payload(decode=True).decode()
                                    # Find verification link using regex
                                    links = re.findall(r'href=[\'"]?([^\'" >]+)[\'"]?', body)
                                    for link in links:
                                        if 'pinterest.com/email/verify' in link:
                                            verification_link = link
                                            break
                        else:
                            body = msg.get_payload(decode=True).decode()
                            links = re.findall(r'href=[\'"]?([^\'" >]+)[\'"]?', body)
                            for link in links:
                                if 'pinterest.com/email/verify' in link:
                                    verification_link = link
                                    break
                
                if not verification_link:
                    logging.info(f"No verification email found yet, waiting {delay} seconds...")
                    time.sleep(delay)
                    attempts += 1
            
            # Close mail connection
            mail.close()
            mail.logout()
            
            if not verification_link:
                logging.error("Failed to find verification link in emails")
                return False
            
            # Click the verification link
            logging.info(f"Found verification link: {verification_link}")
            return self.open_verification_link(verification_link)
            
        except Exception as e:
            logging.error(f"Error verifying Gmail account: {str(e)}")
            return False
    
    def verify_yahoo_account(self, email, password, max_attempts=5, delay=60):
        """Verify Pinterest account using Yahoo Mail
        
        Args:
            email (str): Yahoo email address
            password (str): Yahoo password
            max_attempts (int): Maximum number of attempts to check for verification email
            delay (int): Delay between attempts in seconds
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        try:
            # Connect to Yahoo IMAP server
            mail = imaplib.IMAP4_SSL('imap.mail.yahoo.com')
            mail.login(email, password)
            mail.select('inbox')
            
            # Search for Pinterest verification emails
            verification_link = None
            attempts = 0
            
            while not verification_link and attempts < max_attempts:
                logging.info(f"Checking for verification email (attempt {attempts+1}/{max_attempts})")
                
                # Search for emails from Pinterest
                status, messages = mail.search(None, '(FROM "pinterest@account.pinterest.com" SUBJECT "Verify your email")')
                
                if status == 'OK' and messages[0]:
                    # Get the latest email
                    latest_email_id = messages[0].split()[-1]
                    status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
                    
                    if status == 'OK':
                        # Parse email content
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        # Extract verification link
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == 'text/html':
                                    body = part.get_payload(decode=True).decode()
                                    # Find verification link using regex
                                    links = re.findall(r'href=[\'"]?([^\'" >]+)[\'"]?', body)
                                    for link in links:
                                        if 'pinterest.com/email/verify' in link:
                                            verification_link = link
                                            break
                        else:
                            body = msg.get_payload(decode=True).decode()
                            links = re.findall(r'href=[\'"]?([^\'" >]+)[\'"]?', body)
                            for link in links:
                                if 'pinterest.com/email/verify' in link:
                                    verification_link = link
                                    break
                
                if not verification_link:
                    logging.info(f"No verification email found yet, waiting {delay} seconds...")
                    time.sleep(delay)
                    attempts += 1
            
            # Close mail connection
            mail.close()
            mail.logout()
            
            if not verification_link:
                logging.error("Failed to find verification link in emails")
                return False
            
            # Click the verification link
            logging.info(f"Found verification link: {verification_link}")
            return self.open_verification_link(verification_link)
            
        except Exception as e:
            logging.error(f"Error verifying Yahoo account: {str(e)}")
            return False
    
    def verify_outlook_account(self, email, password, max_attempts=5, delay=60):
        """Verify Pinterest account using Outlook/Hotmail
        
        Args:
            email (str): Outlook/Hotmail email address
            password (str): Outlook/Hotmail password
            max_attempts (int): Maximum number of attempts to check for verification email
            delay (int): Delay between attempts in seconds
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        try:
            # Connect to Outlook IMAP server
            mail = imaplib.IMAP4_SSL('outlook.office365.com')
            mail.login(email, password)
            mail.select('inbox')
            
            # Search for Pinterest verification emails
            verification_link = None
            attempts = 0
            
            while not verification_link and attempts < max_attempts:
                logging.info(f"Checking for verification email (attempt {attempts+1}/{max_attempts})")
                
                # Search for emails from Pinterest
                status, messages = mail.search(None, '(FROM "pinterest@account.pinterest.com" SUBJECT "Verify your email")')
                
                if status == 'OK' and messages[0]:
                    # Get the latest email
                    latest_email_id = messages[0].split()[-1]
                    status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
                    
                    if status == 'OK':
                        # Parse email content
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        # Extract verification link
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == 'text/html':
                                    body = part.get_payload(decode=True).decode()
                                    # Find verification link using regex
                                    links = re.findall(r'href=[\'"]?([^\'" >]+)[\'"]?', body)
                                    for link in links:
                                        if 'pinterest.com/email/verify' in link:
                                            verification_link = link
                                            break
                        else:
                            body = msg.get_payload(decode=True).decode()
                            links = re.findall(r'href=[\'"]?([^\'" >]+)[\'"]?', body)
                            for link in links:
                                if 'pinterest.com/email/verify' in link:
                                    verification_link = link
                                    break
                
                if not verification_link:
                    logging.info(f"No verification email found yet, waiting {delay} seconds...")
                    time.sleep(delay)
                    attempts += 1
            
            # Close mail connection
            mail.close()
            mail.logout()
            
            if not verification_link:
                logging.error("Failed to find verification link in emails")
                return False
            
            # Click the verification link
            logging.info(f"Found verification link: {verification_link}")
            return self.open_verification_link(verification_link)
            
        except Exception as e:
            logging.error(f"Error verifying Outlook account: {str(e)}")
            return False
    
    def open_verification_link(self, verification_link):
        """Open the verification link in a browser and confirm verification
        
        Args:
            verification_link (str): The verification link from the email
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        try:
            # Set up driver if not already set up
            if not self.driver:
                self.setup_driver()
            
            # Open the verification link
            logging.info("Opening verification link in browser")
            self.driver.get(verification_link)
            time.sleep(5)  # Wait for page to load
            
            # Check if verification was successful
            success_indicators = [
                "email verified",
                "verification successful",
                "account confirmed",
                "pinterest.com/homefeed"
            ]
            
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url
            
            for indicator in success_indicators:
                if indicator in page_source or indicator in current_url.lower():
                    logging.info("Email verification successful")
                    return True
            
            # Check if there's a button to complete verification
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    button_text = button.text.lower()
                    if "confirm" in button_text or "verify" in button_text or "continue" in button_text:
                        logging.info(f"Clicking button: {button.text}")
                        button.click()
                        time.sleep(3)
                        
                        # Check again for success indicators
                        page_source = self.driver.page_source.lower()
                        current_url = self.driver.current_url
                        
                        for indicator in success_indicators:
                            if indicator in page_source or indicator in current_url.lower():
                                logging.info("Email verification successful after clicking button")
                                return True
            except Exception as e:
                logging.warning(f"Error clicking verification button: {str(e)}")
            
            logging.warning("Could not confirm if verification was successful")
            return False
            
        except Exception as e:
            logging.error(f"Error opening verification link: {str(e)}")
            return False
    
    def verify_email(self, email, password, email_provider=None):
        """Verify Pinterest account email based on email provider
        
        Args:
            email (str): Email address
            password (str): Email password
            email_provider (str, optional): Email provider (gmail, yahoo, outlook)
                If None, will be detected from email address
                
        Returns:
            bool: True if verification was successful, False otherwise
        """
        try:
            # Detect email provider if not specified
            if not email_provider:
                if "gmail" in email:
                    email_provider = "gmail"
                elif "yahoo" in email:
                    email_provider = "yahoo"
                elif "hotmail" in email or "outlook" in email or "live" in email:
                    email_provider = "outlook"
                else:
                    logging.error(f"Unsupported email provider for {email}")
                    return False
            
            # Verify based on email provider
            if email_provider == "gmail":
                return self.verify_gmail_account(email, password)
            elif email_provider == "yahoo":
                return self.verify_yahoo_account(email, password)
            elif email_provider == "outlook":
                return self.verify_outlook_account(email, password)
            else:
                logging.error(f"Unsupported email provider: {email_provider}")
                return False
                
        except Exception as e:
            logging.error(f"Error verifying email: {str(e)}")
            return False
        finally:
            # Always close the driver
            self.close()

# Example usage
def main():
    """Main function to demonstrate usage"""
    try:
        # Create an instance of EmailVerifier
        verifier = EmailVerifier(headless=False)  # Set to True for headless mode
        
        # Example email and password (replace with actual credentials)
        email = "example@gmail.com"
        password = "your_password"
        
        # Verify email
        success = verifier.verify_email(email, password)
        
        if success:
            print("Email verification successful!")
        else:
            print("Email verification failed.")
        
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    main()