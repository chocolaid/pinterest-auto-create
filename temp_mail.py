import requests
import time
import json
import re
import urllib3
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib.parse

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TempMail:
    def __init__(self, min_len=10, max_len=10):
        self.base_url = "http://localhost:3000"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/json"
        }
        self.min_len = min_len
        self.max_len = max_len
        self.email = None
        self.session_id = None
        self.inbox = []

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[500, 502, 503, 504]  # HTTP status codes to retry on
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        # Disable SSL verification for development
        self.session.verify = False

    def create_email(self, max_retries=3):
        """Create a new temporary email address with retry mechanism"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.base_url}/create-email",
                    headers=self.headers,
                    timeout=30,
                    verify=False
                )
                
                if response.ok:
                    data = response.json()
                    self.email = data.get("email")
                    self.session_id = data.get("sessionId")
                    logging.info(f"Successfully created email: {self.email}")
                    return self.email
                else:
                    logging.warning(f"Failed to create email (attempt {attempt + 1}/{max_retries}): {response.text}")
            except Exception as e:
                logging.warning(f"Error creating email (attempt {attempt + 1}/{max_retries}): {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                
        raise Exception(f"Failed to create email after {max_retries} attempts")

    def get_inbox(self, max_retries=3):
        """Get all messages in the inbox with retry mechanism"""
        if not self.session_id:
            raise Exception("Session ID not found. Create email first.")
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.base_url}/get-inbox/{self.session_id}",
                    headers=self.headers,
                    timeout=30,
                    verify=False
                )
                
                if response.ok:
                    data = response.json()
                    self.inbox = data.get("inbox", [])
                    return self.inbox
                else:
                    error_data = response.json()
                    if error_data.get("error") == "Session not found":
                        logging.warning(f"Session not found, recreating email (attempt {attempt + 1}/{max_retries})")
                        self.create_email()  # Recreate the email
                        continue
                    logging.warning(f"Failed to get inbox (attempt {attempt + 1}/{max_retries}): {response.text}")
            except Exception as e:
                logging.warning(f"Error getting inbox (attempt {attempt + 1}/{max_retries}): {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                
        raise Exception(f"Failed to get inbox after {max_retries} attempts")

    def wait_for_message(self, subject_keyword="", timeout=60, check_interval=5, verbose=False):
        """Wait for a message with specific subject keyword"""
        if not self.session_id:
            raise Exception("Session ID not found. Create email first.")
            
        elapsed = 0
        while elapsed < timeout:
            if verbose:
                print(f"Checking inbox at {elapsed}s...")
            
            try:
                messages = self.get_inbox()
                for msg in messages:
                    subject = msg.get("subject", "")
                    if isinstance(subject, str) and subject_keyword.lower() in subject.lower():
                        if verbose:
                            print("Match found!")
                        return msg
            except Exception as e:
                if verbose:
                    print(f"Error checking inbox: {str(e)}")
            
            time.sleep(check_interval)
            elapsed += check_interval
            
        if verbose:
            print("Timeout reached, no matching message.")
        return None

    def get_message_by_subject(self, keyword):
        """Get a message by subject keyword"""
        if not self.inbox:
            self.get_inbox()
            
        for msg in self.inbox:
            subject = msg.get("subject", "")
            if isinstance(subject, str) and keyword.lower() in subject.lower():
                return msg
        return None

    def extract_links(self, message=None):
        """Extract links from an email message"""
        if message is None:
            if not self.inbox:
                self.get_inbox()
            if not self.inbox:
                return []
            message = self.inbox[0]
        
        if isinstance(message, dict) and 'snippet' in message:
            body = message.get("snippet", "")
            
            # For Pinterest verification emails
            if 'pinterest' in message.get('from', '').lower() and 'verify' in body.lower():
                # Look for the verification URL in the target parameter
                target_pattern = r'target=(https?%3A%2F%2F[^&\s"]+)'
                target_matches = re.findall(target_pattern, body)
                
                for target in target_matches:
                    try:
                        decoded = urllib.parse.unquote(target)
                        if 'pinterest.com' in decoded and 'verify' in decoded:
                            # Extract code and uid
                            code_match = re.search(r'code=([a-f0-9]{32})', decoded)
                            uid_match = re.search(r'uid=(\d+)', decoded)
                            
                            if code_match and uid_match:
                                code = code_match.group(1)
                                uid = uid_match.group(1)
                                verification_url = f"https://www.pinterest.com/verify?code={code}&uid={uid}"
                                return [verification_url]
                    except:
                        continue
                
                # If we couldn't find it in target parameter, try direct URL
                direct_url_pattern = r'https://www\.pinterest\.com/secure/autologin/[^"\s]+verify[^"\s]+code=[^"\s]+uid=[^"\s]+'
                direct_urls = re.findall(direct_url_pattern, body, re.IGNORECASE | re.DOTALL)
                if direct_urls:
                    return [direct_urls[0]]
            
            # For non-Pinterest emails or if verification URL not found
            return re.findall(r'https?://[^\s<>"\']+', body)
        
        return []

    def to_json(self, filepath="inbox.json"):
        """Save inbox to JSON file"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.inbox, f, indent=2)
        return filepath

    def __str__(self):
        return f"TempMail({self.email}) with {len(self.inbox)} messages"

    def latest_subjects(self, limit=5):
        """Get latest message subjects"""
        self.get_inbox()
        return [msg.get("subject") for msg in self.inbox[:limit]]

    def close(self):
        """Close the session"""
        if self.session_id:
            try:
                self.session.post(
                    f"{self.base_url}/kill-session/{self.session_id}",
                    headers=self.headers,
                    timeout=30,
                    verify=False
                )
                self.session_id = None
                self.email = None
                self.inbox = []
            except Exception as e:
                logging.warning(f"Error closing session: {str(e)}")

def debug_example_inbox():
    """Debug function to analyze example_inbox.json in detail"""
    print("Analyzing example_inbox.json in detail...")
    
    try:
        with open("example_inbox.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Found {len(data)} messages in example_inbox.json")
        
        for i, message in enumerate(data):
            print(f"\nMessage {i+1}:")
            print(f"  From: {message.get('from', 'N/A')}")
            print(f"  Subject: {message.get('subject', 'N/A')}")
            
            # Find verification info
            body_text = message.get('body_text', '')
            
            # Find code and uid
            verify_codes = re.findall(r'code=([a-f0-9]{32})', body_text)
            uid_matches = re.findall(r'uid=(\d+)', body_text)
            
            if verify_codes:
                print(f"  Verification code: {verify_codes[0]}")
            if uid_matches:
                print(f"  User ID: {uid_matches[0]}")
            
            # Look for autologin URLs
            autologin_urls = re.findall(r'(https://www\.pinterest\.com/secure/autologin/[^\s"\'<>]+)', body_text)
            if autologin_urls:
                print(f"  Found {len(autologin_urls)} autologin URLs")
                for url in autologin_urls[:1]:  # Show just the first one
                    print(f"  Sample autologin URL: {url[:100]}...")
            
            # Look for target parameters
            target_matches = re.findall(r'target=(https?%3A%2F%2F[^&\s]+)', body_text)
            if target_matches:
                print(f"  Found {len(target_matches)} target parameters")
                
                for target in target_matches[:1]:  # Show just the first one
                    try:
                        decoded = urllib.parse.unquote(target)
                        print(f"  Decoded target: {decoded[:100]}...")
                        
                        # Check for verification in the decoded target
                        if 'verify' in decoded:
                            print("  ✓ Target contains 'verify'")
                        if 'autologin' in decoded:
                            print("  ✓ Target contains 'autologin'")
                        if 'next=' in decoded:
                            print("  ✓ Target contains 'next='")
                    except Exception as e:
                        print(f"  Error decoding target: {str(e)}")

    except Exception as e:
        print(f"Error analyzing example_inbox.json: {str(e)}")

# Example usage
if __name__ == "__main__":
    temp_mail = TempMail()
    
    # First run the regular test
    print("Running standard parsing test...")
    try:
        results = temp_mail.test_parsing()
        print(f"Parsing test results: {'Success' if results['success'] else 'Failed'}")
        print(f"Found {results['pinterest_emails']} Pinterest emails")
        print(f"Found {len(results['verification_links'])} verification links")
        
        # Print the first verification link if any
        if results['verification_links']:
            first_link = results['verification_links'][0]
            print(f"Sample verification link ({first_link['type']}): {first_link['url'][:100]}...")
    except Exception as e:
        print(f"Error testing parsing: {str(e)}")
    
    # Then run the detailed debug
    print("\n" + "="*50)
    debug_example_inbox()
    
    # Uncomment to test actual email generation
    # email = temp_mail.create_email()
    # print(f"Generated email: {email}")
    # print("Waiting for messages...")
    # message = temp_mail.wait_for_message(timeout=60, verbose=True)
    # if message:
    #     print(f"Received message: {message.get('subject')}")
    #     links = temp_mail.extract_links(message)
    #     print(f"Found links: {links}")
    # else:
    #     print("No messages received.")
