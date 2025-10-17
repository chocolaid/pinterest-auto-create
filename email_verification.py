import os
import time
import json
import logging
import re
import imaplib
import email
from email.header import decode_header
import random
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from temp_mail import TempMail

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
    
    def __init__(self, headless=True, use_existing_driver=False, driver=None):
        """Initialize the email verifier
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            use_existing_driver (bool): Whether to use an existing WebDriver instance
            driver: An existing WebDriver instance
        """
        self.headless = headless
        self.driver = driver if use_existing_driver else None
        self.wait = None
        self.temp_mail = None
        self._use_existing_driver = use_existing_driver
        
        # Only setup a new driver if we're not using an existing one
        if not use_existing_driver:
            self.setup_driver()
        else:
            # If using existing driver, just setup the wait
            if self.driver:
                self.wait = WebDriverWait(self.driver, 15)
        
    def setup_driver(self):
        """Set up undetected Selenium WebDriver"""
        try:
            # Configure Chrome options
            options = uc.ChromeOptions()
            
            # Add headless option if specified
            if self.headless:
                options.add_argument("--headless=new")
            
            # Add standard options for performance and stability
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-notifications")
            
            # Initialize undetected_chromedriver
            self.driver = uc.Chrome(
                options=options,
                headless=self.headless,
                use_subprocess=True,
            )
            
            # Set window size
            self.driver.set_window_size(1366, 768)
            
            # Set up WebDriverWait
            self.wait = WebDriverWait(self.driver, 15)
            
            logging.info("WebDriver initialized successfully for email verification")
        except Exception as e:
            logging.error(f"Failed to initialize WebDriver for email verification: {str(e)}")
            raise
    
    def close(self):
        """Close the WebDriver"""
        # Only close the driver if we created it (not if it was passed to us)
        if self.driver and not self._use_existing_driver:
            self.driver.quit()
            logging.info("WebDriver closed")
    
        # Close temp mail session if it exists
        if self.temp_mail:
            self.temp_mail.close()
            self.temp_mail = None
    
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

    def generate_temp_mail(self, min_len=10, max_len=10):
        """Generate a temporary email address"""
        try:
            self.temp_mail = TempMail(min_len=min_len, max_len=max_len)
            self.email = self.temp_mail.create_email()
            logging.info(f"Generated temporary email: {self.email}")
            return self.email
        except Exception as e:
            logging.error(f"Failed to generate temporary email: {str(e)}")
            raise
    
    def verify_with_temp_mail(self, timeout=300, check_interval=60, verbose=True):
        """Verify Pinterest account using temporary email
        
        Args:
            timeout (int): Maximum time to wait for verification email in seconds
            check_interval (int): Time between email checks in seconds
            verbose (bool): Whether to print verbose output
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        try:
            if not self.temp_mail:
                logging.error("Temporary email not generated. Call generate_temp_mail first.")
                return False
                
            logging.info(f"Waiting for Pinterest verification email...")
            
            # Wait for verification email from Pinterest
            message = self.temp_mail.wait_for_message(
                subject_keyword="Please confirm your email",
                timeout=timeout,
                check_interval=check_interval,
                verbose=verbose
            )
            
            if not message:
                logging.error("No verification email received")
                return False
                
            logging.info("Verification email received, extracting verification link")
            
            # Extract verification link from the message
            verification_link = None
            
            # Check if we got a message in the expected format
            if isinstance(message, dict) and 'body_text' in message:
                # Extract URLs from the body text
                body_text = message['body_text']
                urls = self.temp_mail.extract_links(message)
                
                # Find the verification URL
                for url in urls:
                    if 'pinterest.com' in url and '/verify' in url:
                        verification_link = url
                        break
                        
                # If we didn't find a direct verification URL, look for the autologin URL
                if not verification_link:
                    for url in urls:
                        if 'pinterest.com' in url and '/autologin/' in url and 'next=' in url and 'verify' in url:
                            verification_link = url
                            break
                
                # If still no verification link, try more targeted approaches
                if not verification_link:
                    # Look for target parameters with encoded autologin URLs
                    targets = re.findall(r'target=(https?%3A%2F%2F[^&\s]+)', body_text)
                    
                    for target in targets:
                        try:
                            import urllib.parse
                            decoded = urllib.parse.unquote(target)
                            # Check if this contains the verification info
                            if 'autologin' in decoded and 'next=' in decoded and 'verify' in decoded:
                                verification_link = decoded
                                break
                        except:
                            pass
                    
                    # If still not found, try direct search for patterns
                    if not verification_link:
                        verify_codes = re.findall(r'code=([a-f0-9]{32})', body_text)
                        if verify_codes:
                            verify_code = verify_codes[0]
                            uid_matches = re.findall(r'uid=(\d+)', body_text)
                            if uid_matches:
                                uid = uid_matches[0]
                                # Construct the verification URL
                                verification_link = f"https://www.pinterest.com/verify?code={verify_code}&uid={uid}"
            
            if not verification_link:
                logging.error("No verification link found in email")
                return False
                
            logging.info(f"Found verification link: {verification_link}")
            
            # Use verification link
            return self.open_verification_link(verification_link)
            
        except Exception as e:
            logging.error(f"Error in temp mail verification: {str(e)}")
            return False
    
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
        """Open the verification link in the browser
        
        Args:
            verification_link (str): The verification link to open
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        try:
            if not self.driver:
                self.setup_driver()
            
            logging.info(f"Opening verification link: {verification_link}")
            self.driver.get(verification_link)
            
            # Wait for the page to load
            time.sleep(5)
            
            # Check if verification was successful
            current_url = self.driver.current_url
            
            # Check for success indicators in URL or page content
            success_indicators = [
                "pinterest.com/homefeed",
                "pinterest.com/settings",
                "pinterest.com/following",
                "pinterest.com/"
            ]
            
            for indicator in success_indicators:
                if indicator in current_url:
                    logging.info(f"Verification successful, redirected to: {current_url}")
                    return True
            
            # Check for success message on the page
            try:
                success_element = self.wait_for_element(By.XPATH, "//*[contains(text(), 'verified') or contains(text(), 'confirmed') or contains(text(), 'success')]", timeout=5)
                if success_element:
                    logging.info("Verification success message found on page")
                    return True
            except:
                pass
            
            logging.warning(f"Could not confirm successful verification. Current URL: {current_url}")
            return False
            
        except Exception as e:
            logging.error(f"Error opening verification link: {str(e)}")
            return False
    
    def verify_email(self, email, password=None, email_provider=None):
        """Verify a Pinterest account email
        
        Args:
            email (str): Email address
            password (str, optional): Email password (not needed for temp mail)
            email_provider (str, optional): Email provider ('gmail', 'yahoo', 'outlook', 'temp_mail')
                If not provided, will try to determine from email domain
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        if not email_provider:
            # Determine email provider from domain
            domain = email.split('@')[-1].lower()
            
            if domain == 'gmail.com':
                email_provider = 'gmail'
            elif domain in ['yahoo.com', 'ymail.com']:
                email_provider = 'yahoo'
            elif domain in ['outlook.com', 'hotmail.com', 'live.com']:
                email_provider = 'outlook'
            elif 'temp-mail.io' in domain:
                email_provider = 'temp_mail'
            else:
                logging.warning(f"Unknown email provider for domain {domain}, will attempt to use temp_mail")
                email_provider = 'temp_mail'
        
        logging.info(f"Verifying email {email} using {email_provider}")
        
        # Verify based on email provider
        if email_provider == 'gmail':
            if not password:
                logging.error("Password required for Gmail verification")
                return False
            return self.verify_gmail_account(email, password)
            
        elif email_provider == 'yahoo':
            if not password:
                logging.error("Password required for Yahoo verification")
                return False
            return self.verify_yahoo_account(email, password)
            
        elif email_provider == 'outlook':
            if not password:
                logging.error("Password required for Outlook verification")
                return False
            return self.verify_outlook_account(email, password)
            
        elif email_provider == 'temp_mail':
            return self.verify_with_temp_mail()
            
        else:
            logging.error(f"Unsupported email provider: {email_provider}")
            return False

def main():
    """Main function to demonstrate usage"""
    try:
        verifier = EmailVerifier(headless=False)
        
        # Generate a temporary email
        email = verifier.generate_temp_mail()
        print(f"Generated email: {email}")
        
        # You would typically use this email during account creation,
        # then call verify_with_temp_mail afterward.
        # This is a simulation:
        success = verifier.verify_with_temp_mail(timeout=180)
        
        if success:
            print("Email verification successful!")
        else:
            print("Email verification failed!")
        
        verifier.close()
        
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    main()