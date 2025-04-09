import os
import time
import logging
import random
import base64
import requests
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("captcha_solver.log"),
        logging.StreamHandler()
    ]
)

class CaptchaSolver:
    """A class to handle CAPTCHA solving for Pinterest account creation"""
    
    def __init__(self, api_key=None, service="2captcha"):
        """Initialize the CAPTCHA solver
        
        Args:
            api_key (str, optional): API key for the CAPTCHA solving service
            service (str): CAPTCHA solving service to use (2captcha, anticaptcha, etc.)
        """
        self.api_key = api_key
        self.service = service.lower()
        self.base_url = self._get_service_url()
        
    def _get_service_url(self):
        """Get the base URL for the selected CAPTCHA solving service
        
        Returns:
            str: Base URL for the service API
        """
        if self.service == "2captcha":
            return "https://2captcha.com/in.php"
        elif self.service == "anticaptcha":
            return "https://api.anti-captcha.com/createTask"
        else:
            logging.warning(f"Unknown service: {self.service}, defaulting to 2captcha")
            return "https://2captcha.com/in.php"
    
    def solve_recaptcha(self, site_key, page_url, driver=None):
        """Solve reCAPTCHA using the selected service
        
        Args:
            site_key (str): The reCAPTCHA site key
            page_url (str): The URL of the page with the CAPTCHA
            driver (webdriver, optional): Selenium WebDriver instance
            
        Returns:
            str: The CAPTCHA solution or None if failed
        """
        if not self.api_key:
            logging.error("No API key provided for CAPTCHA solving service")
            return self._try_manual_solve(driver)
        
        try:
            if self.service == "2captcha":
                return self._solve_with_2captcha(site_key, page_url)
            elif self.service == "anticaptcha":
                return self._solve_with_anticaptcha(site_key, page_url)
            else:
                logging.warning(f"Unsupported service: {self.service}, trying 2captcha")
                return self._solve_with_2captcha(site_key, page_url)
        except Exception as e:
            logging.error(f"Error solving reCAPTCHA: {str(e)}")
            return self._try_manual_solve(driver)
    
    def _solve_with_2captcha(self, site_key, page_url):
        """Solve reCAPTCHA using 2captcha service
        
        Args:
            site_key (str): The reCAPTCHA site key
            page_url (str): The URL of the page with the CAPTCHA
            
        Returns:
            str: The CAPTCHA solution or None if failed
        """
        # Submit CAPTCHA for solving
        params = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1
        }
        
        response = requests.get(self.base_url, params=params)
        if response.status_code != 200:
            logging.error(f"Error submitting CAPTCHA: {response.text}")
            return None
        
        result = response.json()
        if result.get('status') != 1:
            logging.error(f"Error submitting CAPTCHA: {result.get('request')}")
            return None
        
        request_id = result.get('request')
        logging.info(f"CAPTCHA submitted, request ID: {request_id}")
        
        # Wait for solution
        for _ in range(30):  # Try for 5 minutes (30 * 10 seconds)
            time.sleep(10)  # Wait 10 seconds between checks
            
            response = requests.get(
                'https://2captcha.com/res.php',
                params={
                    'key': self.api_key,
                    'action': 'get',
                    'id': request_id,
                    'json': 1
                }
            )
            
            if response.status_code != 200:
                continue
            
            result = response.json()
            if result.get('status') == 1:
                return result.get('request')
            
            if result.get('request') != 'CAPCHA_NOT_READY':
                logging.error(f"Error getting CAPTCHA solution: {result.get('request')}")
                return None
        
        logging.error("Timeout waiting for CAPTCHA solution")
        return None
    
    def _solve_with_anticaptcha(self, site_key, page_url):
        """Solve reCAPTCHA using Anti-Captcha service
        
        Args:
            site_key (str): The reCAPTCHA site key
            page_url (str): The URL of the page with the CAPTCHA
            
        Returns:
            str: The CAPTCHA solution or None if failed
        """
        # Submit CAPTCHA for solving
        payload = {
            'clientKey': self.api_key,
            'task': {
                'type': 'NoCaptchaTaskProxyless',
                'websiteURL': page_url,
                'websiteKey': site_key
            }
        }
        
        response = requests.post(self.base_url, json=payload)
        if response.status_code != 200:
            logging.error(f"Error submitting CAPTCHA: {response.text}")
            return None
        
        result = response.json()
        if result.get('errorId') != 0:
            logging.error(f"Error submitting CAPTCHA: {result.get('errorDescription')}")
            return None
        
        task_id = result.get('taskId')
        logging.info(f"CAPTCHA submitted, task ID: {task_id}")
        
        # Wait for solution
        for _ in range(30):  # Try for 5 minutes (30 * 10 seconds)
            time.sleep(10)  # Wait 10 seconds between checks
            
            response = requests.post(
                'https://api.anti-captcha.com/getTaskResult',
                json={
                    'clientKey': self.api_key,
                    'taskId': task_id
                }
            )
            
            if response.status_code != 200:
                continue
            
            result = response.json()
            if result.get('status') == 'ready':
                return result.get('solution', {}).get('gRecaptchaResponse')
            
            if result.get('errorId') != 0:
                logging.error(f"Error getting CAPTCHA solution: {result.get('errorDescription')}")
                return None
        
        logging.error("Timeout waiting for CAPTCHA solution")
        return None
    
    def _try_manual_solve(self, driver):
        """Try to solve CAPTCHA manually if a driver is provided
        
        Args:
            driver (webdriver, optional): Selenium WebDriver instance
            
        Returns:
            str: The CAPTCHA solution or None if failed
        """
        if not driver:
            logging.warning("No WebDriver provided for manual CAPTCHA solving")
            return None
        
        try:
            # Check if we're in headless mode
            if driver.execute_script("return navigator.webdriver") is not None:
                logging.warning("Cannot solve CAPTCHA manually in headless mode")
                return None
            
            # Wait for manual solving (up to 2 minutes)
            logging.info("Waiting for manual CAPTCHA solving (up to 2 minutes)...")
            
            # Try to find the CAPTCHA iframe
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title*='recaptcha' i]"))
            )
            
            # Switch to the iframe
            driver.switch_to.frame(iframe)
            
            # Wait for the checkbox to be clickable
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".recaptcha-checkbox-border"))
            )
            
            # Click the checkbox
            checkbox.click()
            
            # Switch back to the main content
            driver.switch_to.default_content()
            
            # Wait for manual solving
            for _ in range(120):  # 2 minutes
                # Check if CAPTCHA is solved by looking for the CAPTCHA response
                try:
                    g_response = driver.execute_script(
                        "return document.getElementById('g-recaptcha-response').value;"
                    )
                    if g_response and len(g_response) > 0:
                        logging.info("CAPTCHA solved manually")
                        return g_response
                except Exception:
                    pass
                
                time.sleep(1)
            
            logging.warning("Timeout waiting for manual CAPTCHA solving")
            return None
            
        except Exception as e:
            logging.error(f"Error in manual CAPTCHA solving: {str(e)}")
            return None
    
    def solve_image_captcha(self, image_element=None, image_url=None, image_path=None, driver=None):
        """Solve image-based CAPTCHA
        
        Args:
            image_element (WebElement, optional): Selenium WebElement containing the CAPTCHA image
            image_url (str, optional): URL of the CAPTCHA image
            image_path (str, optional): Path to the CAPTCHA image file
            driver (webdriver, optional): Selenium WebDriver instance
            
        Returns:
            str: The CAPTCHA solution or None if failed
        """
        if not self.api_key:
            logging.error("No API key provided for CAPTCHA solving service")
            return self._try_manual_image_solve(driver)
        
        try:
            # Get the image data
            image_data = None
            
            if image_element and driver:
                # Take screenshot of the element
                image_data = self._get_element_image(image_element, driver)
            elif image_url:
                # Download image from URL
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_data = BytesIO(response.content)
            elif image_path and os.path.exists(image_path):
                # Read image from file
                with open(image_path, 'rb') as f:
                    image_data = BytesIO(f.read())
            
            if not image_data:
                logging.error("Could not get CAPTCHA image data")
                return self._try_manual_image_solve(driver)
            
            # Encode image to base64
            image = Image.open(image_data)
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Submit to solving service
            if self.service == "2captcha":
                return self._solve_image_with_2captcha(img_str)
            elif self.service == "anticaptcha":
                return self._solve_image_with_anticaptcha(img_str)
            else:
                logging.warning(f"Unsupported service: {self.service}, trying 2captcha")
                return self._solve_image_with_2captcha(img_str)
                
        except Exception as e:
            logging.error(f"Error solving image CAPTCHA: {str(e)}")
            return self._try_manual_image_solve(driver)
    
    def _get_element_image(self, element, driver):
        """Get image data from a WebElement
        
        Args:
            element (WebElement): Selenium WebElement containing the image
            driver (webdriver): Selenium WebDriver instance
            
        Returns:
            BytesIO: Image data or None if failed
        """
        try:
            # Get element location and size
            location = element.location
            size = element.size
            
            # Take screenshot of the page
            screenshot = driver.get_screenshot_as_png()
            screenshot = Image.open(BytesIO(screenshot))
            
            # Calculate element boundaries
            left = location['x']
            top = location['y']
            right = location['x'] + size['width']
            bottom = location['y'] + size['height']
            
            # Crop the screenshot to the element
            image = screenshot.crop((left, top, right, bottom))
            
            # Save to BytesIO
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            buffered.seek(0)
            
            return buffered
            
        except Exception as e:
            logging.error(f"Error getting element image: {str(e)}")
            return None
    
    def _solve_image_with_2captcha(self, base64_image):
        """Solve image CAPTCHA using 2captcha service
        
        Args:
            base64_image (str): Base64-encoded image data
            
        Returns:
            str: The CAPTCHA solution or None if failed
        """
        # Submit CAPTCHA for solving
        params = {
            'key': self.api_key,
            'method': 'base64',
            'body': base64_image,
            'json': 1
        }
        
        response = requests.post(self.base_url, data=params)
        if response.status_code != 200:
            logging.error(f"Error submitting image CAPTCHA: {response.text}")
            return None
        
        result = response.json()
        if result.get('status') != 1:
            logging.error(f"Error submitting image CAPTCHA: {result.get('request')}")
            return None
        
        request_id = result.get('request')
        logging.info(f"Image CAPTCHA submitted, request ID: {request_id}")
        
        # Wait for solution
        for _ in range(30):  # Try for 5 minutes (30 * 10 seconds)
            time.sleep(10)  # Wait 10 seconds between checks
            
            response = requests.get(
                'https://2captcha.com/res.php',
                params={
                    'key': self.api_key,
                    'action': 'get',
                    'id': request_id,
                    'json': 1
                }
            )
            
            if response.status_code != 200:
                continue
            
            result = response.json()
            if result.get('status') == 1:
                return result.get('request')
            
            if result.get('request') != 'CAPCHA_NOT_READY':
                logging.error(f"Error getting image CAPTCHA solution: {result.get('request')}")
                return None
        
        logging.error("Timeout waiting for image CAPTCHA solution")
        return None
    
    def _solve_image_with_anticaptcha(self, base64_image):
        """Solve image CAPTCHA using Anti-Captcha service
        
        Args:
            base64_image (str): Base64-encoded image data
            
        Returns:
            str: The CAPTCHA solution or None if failed
        """
        # Submit CAPTCHA for solving
        payload = {
            'clientKey': self.api_key,
            'task': {
                'type': 'ImageToTextTask',
                'body': base64_image,
                'phrase': False,
                'case': False,
                'numeric': 0,
                'math': False,
                'minLength': 0,
                'maxLength': 0
            }
        }
        
        response = requests.post(self.base_url, json=payload)
        if response.status_code != 200:
            logging.error(f"Error submitting image CAPTCHA: {response.text}")
            return None
        
        result = response.json()
        if result.get('errorId') != 0:
            logging.error(f"Error submitting image CAPTCHA: {result.get('errorDescription')}")
            return None
        
        task_id = result.get('taskId')
        logging.info(f"Image CAPTCHA submitted, task ID: {task_id}")
        
        # Wait for solution
        for _ in range(30):  # Try for 5 minutes (30 * 10 seconds)
            time.sleep(10)  # Wait 10 seconds between checks
            
            response = requests.post(
                'https://api.anti-captcha.com/getTaskResult',
                json={
                    'clientKey': self.api_key,
                    'taskId': task_id
                }
            )
            
            if response.status_code != 200:
                continue
            
            result = response.json()
            if result.get('status') == 'ready':
                return result.get('solution', {}).get('text')
            
            if result.get('errorId') != 0:
                logging.error(f"Error getting image CAPTCHA solution: {result.get('errorDescription')}")
                return None
        
        logging.error("Timeout waiting for image CAPTCHA solution")
        return None
    
    def _try_manual_image_solve(self, driver):
        """Try to solve image CAPTCHA manually if a driver is provided
        
        Args:
            driver (webdriver, optional): Selenium WebDriver instance
            
        Returns:
            str: The CAPTCHA solution or None if failed
        """
        if not driver:
            logging.warning("No WebDriver provided for manual image CAPTCHA solving")
            return None
        
        try:
            # Check if we're in headless mode
            if driver.execute_script("return navigator.webdriver") is not None:
                logging.warning("Cannot solve image CAPTCHA manually in headless mode")
                return None
            
            # Wait for manual solving (up to 2 minutes)
            logging.info("Waiting for manual image CAPTCHA solving (up to 2 minutes)...")
            
            # Try to find the CAPTCHA input field
            captcha_input = None
            for selector in ["input[name*='captcha' i]", "input[id*='captcha' i]", "input[placeholder*='captcha' i]"]:
                try:
                    captcha_input = driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha_input:
                        break
                except NoSuchElementException:
                    continue
            
            if not captcha_input:
                logging.warning("Could not find CAPTCHA input field")
                return None
            
            # Wait for manual solving
            for _ in range(120):  # 2 minutes
                # Check if CAPTCHA is solved by looking for input value
                value = captcha_input.get_attribute("value")
                if value and len(value) > 0:
                    logging.info("Image CAPTCHA solved manually")
                    return value
                
                time.sleep(1)
            
            logging.warning("Timeout waiting for manual image CAPTCHA solving")
            return None
            
        except Exception as e:
            logging.error(f"Error in manual image CAPTCHA solving: {str(e)}")
            return None

# Example usage
def main():
    """Main function to demonstrate usage"""
    try:
        # Create an instance of CaptchaSolver
        solver = CaptchaSolver(api_key="your_api_key_here")  # Replace with your actual API key
        
        # Example reCAPTCHA parameters
        site_key = "6LeoeSkTAAAAAA9rkZs5oS82l69OEYjKRZAiKdaF"  # Example site key
        page_url = "https://www.pinterest.com/signup/"  # Example page URL
        
        # Solve reCAPTCHA
        solution = solver.solve_recaptcha(site_key, page_url)
        
        if solution:
            print(f"CAPTCHA solved successfully!")
        else:
            print("Failed to solve CAPTCHA.")
        
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    main()