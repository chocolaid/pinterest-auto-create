import os
import random
import requests
import logging
import json
from utils.logger import setup_logger

# Set up logger
logger = setup_logger("proxy_manager")

class ProxyManager:
    """Class to manage proxies for batch account creation"""
    
    def __init__(self, proxy_file=None, proxy_api_url=None, proxy_api_key=None):
        """Initialize the proxy manager
        
        Args:
            proxy_file (str, optional): Path to file containing proxies
            proxy_api_url (str, optional): URL for proxy API
            proxy_api_key (str, optional): API key for proxy API
        """
        self.proxy_file = proxy_file
        self.proxy_api_url = proxy_api_url
        self.proxy_api_key = proxy_api_key
        self.proxies = []
        self.current_index = 0
        
        # Load proxies if proxy file is provided
        if self.proxy_file and os.path.exists(self.proxy_file):
            self.load_proxies_from_file()
        elif self.proxy_api_url and self.proxy_api_key:
            self.load_proxies_from_api()
    
    def load_proxies_from_file(self):
        """Load proxies from a file"""
        try:
            with open(self.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f.readlines() if line.strip()]
            
            # Validate and format proxies
            self.proxies = [self._format_proxy(proxy) for proxy in self.proxies]
            self.proxies = [p for p in self.proxies if p]  # Remove None values
            
            logger.info(f"Loaded {len(self.proxies)} proxies from {self.proxy_file}")
        except Exception as e:
            logger.error(f"Error loading proxies from file: {str(e)}")
    
    def load_proxies_from_api(self):
        """Load proxies from an API endpoint"""
        try:
            headers = {}
            if self.proxy_api_key:
                headers["Authorization"] = f"Bearer {self.proxy_api_key}"
            
            response = requests.get(self.proxy_api_url, headers=headers)
            
            if response.ok:
                try:
                    # Try to parse as JSON
                    data = response.json()
                    
                    # Handle different API response formats
                    if isinstance(data, list):
                        # If response is a list of proxies
                        self.proxies = data
                    elif isinstance(data, dict) and "proxies" in data:
                        # If response has a "proxies" key
                        self.proxies = data["proxies"]
                    elif isinstance(data, dict) and "data" in data:
                        # If response has a "data" key
                        self.proxies = data["data"]
                    else:
                        # Unknown format
                        logger.warning(f"Unknown API response format: {data}")
                        self.proxies = []
                except:
                    # Try to parse as plain text (one proxy per line)
                    self.proxies = [line.strip() for line in response.text.splitlines() if line.strip()]
                
                # Validate and format proxies
                self.proxies = [self._format_proxy(proxy) for proxy in self.proxies]
                self.proxies = [p for p in self.proxies if p]  # Remove None values
                
                logger.info(f"Loaded {len(self.proxies)} proxies from API")
            else:
                logger.error(f"Failed to load proxies from API: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error loading proxies from API: {str(e)}")
    
    def _format_proxy(self, proxy):
        """Format and validate a proxy string
        
        Args:
            proxy (str or dict): Proxy in string or dictionary format
            
        Returns:
            str: Formatted proxy string or None if invalid
        """
        try:
            # Handle dictionary format
            if isinstance(proxy, dict):
                # Check for different key naming conventions
                ip = proxy.get('ip') or proxy.get('host') or proxy.get('address')
                port = proxy.get('port')
                
                if not (ip and port):
                    return None
                
                protocol = proxy.get('protocol') or proxy.get('type') or 'http'
                username = proxy.get('username') or proxy.get('user')
                password = proxy.get('password') or proxy.get('pass')
                
                # Build proxy string
                if username and password:
                    return f"{protocol}://{username}:{password}@{ip}:{port}"
                else:
                    return f"{protocol}://{ip}:{port}"
            
            # Handle string format
            elif isinstance(proxy, str):
                # Check if the proxy is already formatted with a protocol
                if '://' in proxy:
                    # Make sure the format is correct
                    parts = proxy.split('://')
                    protocol = parts[0].lower()
                    rest = parts[1]
                    
                    # Only return if it's a valid protocol
                    if protocol in ['http', 'https', 'socks4', 'socks5']:
                        return proxy
                    else:
                        # Try to fix with default http protocol
                        return f"http://{rest}"
                else:
                    # Add default protocol
                    return f"http://{proxy}"
            
            # Invalid format
            else:
                return None
        except Exception as e:
            logger.warning(f"Error formatting proxy {proxy}: {str(e)}")
            return None
    
    def get_proxies(self):
        """Get all available proxies
        
        Returns:
            list: List of proxy strings
        """
        return self.proxies
    
    def get_random_proxy(self):
        """Get a random proxy from the list
        
        Returns:
            str: Random proxy or None if no proxies are available
        """
        if not self.proxies:
            logger.warning("No proxies available")
            return None
        
        return random.choice(self.proxies)
    
    def get_next_proxy(self):
        """Get the next proxy in sequence
        
        Returns:
            str: Next proxy or None if no proxies are available
        """
        if not self.proxies:
            logger.warning("No proxies available")
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def test_proxies(self, timeout=10):
        """Test all proxies and remove non-working ones
        
        Args:
            timeout (int): Connection timeout in seconds
            
        Returns:
            int: Number of working proxies
        """
        working_proxies = []
        
        for proxy in self.proxies:
            try:
                # Test the proxy
                proxies = {
                    "http": proxy,
                    "https": proxy
                }
                
                response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=timeout)
                
                if response.ok:
                    working_proxies.append(proxy)
                    logger.info(f"Proxy {proxy} is working")
                else:
                    logger.warning(f"Proxy {proxy} returned status code {response.status_code}")
            except Exception as e:
                logger.warning(f"Proxy {proxy} is not working: {str(e)}")
        
        self.proxies = working_proxies
        self.current_index = 0
        
        logger.info(f"Found {len(self.proxies)} working proxies out of {len(working_proxies)}")
        return len(self.proxies)
    
    def save_proxies(self, output_file="working_proxies.txt"):
        """Save working proxies to a file
        
        Args:
            output_file (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(output_file, 'w') as f:
                for proxy in self.proxies:
                    f.write(f"{proxy}\n")
            
            logger.info(f"Saved {len(self.proxies)} proxies to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving proxies to file: {str(e)}")
            return False 