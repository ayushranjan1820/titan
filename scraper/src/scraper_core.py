"""
Generic, config-driven web scraper for e-commerce product data.
Supports multiple extraction strategies and site configurations.
"""

import httpx
import yaml
import time
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductScraper:
    """
    Generic product scraper that reads configuration from YAML files.
    Designed to be site-agnostic and reusable across product categories.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize scraper with configuration file.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        self.products = []
        self.errors = []
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate configuration from YAML file."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate required fields
        required = ['site_name', 'category', 'start_urls', 'selectors']
        for field in required:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")
        
        return config
    
    def _rate_limit(self):
        """Apply rate limiting based on config."""
        rate_config = self.config.get('rate_limit', {})
        delay = rate_config.get('delay_between_pages', 1.0)
        time.sleep(delay)
    
    def _extract_text(self, soup: BeautifulSoup, selector: str, extract_all: bool = False) -> Optional[Any]:
        """
        Extract text from HTML using CSS selector.
        
        Args:
            soup: BeautifulSoup object
            selector: CSS selector
            extract_all: If True, extract all matching elements
            
        Returns:
            Extracted text or list of texts
        """
        try:
            # Handle attribute extraction (e.g., "img::attr(src)")
            attr_match = re.match(r'(.+)::attr\((.+)\)', selector)
            if attr_match:
                css_selector, attr_name = attr_match.groups()
                if extract_all:
                    elements = soup.select(css_selector)
                    return [elem.get(attr_name, '').strip() for elem in elements if elem.get(attr_name)]
                else:
                    elem = soup.select_one(css_selector)
                    return elem.get(attr_name, '').strip() if elem else None
            
            # Standard text extraction
            if extract_all:
                elements = soup.select(selector)
                texts = [elem.get_text(strip=True) for elem in elements]
                return [t for t in texts if t]  # Filter empty strings
            else:
                elem = soup.select_one(selector)
                return elem.get_text(strip=True) if elem else None
                
        except Exception as e:
            logger.debug(f"Error extracting with selector '{selector}': {e}")
            return None if not extract_all else []
    
    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text."""
        if not text:
            return None
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text if text else None
    
    def _parse_price(self, price_str: Optional[str]) -> Optional[float]:
        """Extract numeric price from string."""
        if not price_str:
            return None
        
        # Remove currency symbols and commas
        price_clean = re.sub(r'[^\d.]', '', price_str)
        
        try:
            return float(price_clean)
        except ValueError:
            return None
    
    def _get_next_page_url(self, current_url: str, page_num: int) -> Optional[str]:
        """
        Generate next page URL based on pagination config.
        
        Args:
            current_url: Current page URL
            page_num: Next page number
            
        Returns:
            Next page URL or None if max pages reached
        """
        pagination = self.config.get('pagination', {})
        max_pages = pagination.get('max_pages', 10)
        
        if page_num > max_pages:
            return None
        
        pag_type = pagination.get('type', 'url_param')
        
        if pag_type == 'url_param':
            param_name = pagination.get('param_name', 'page')
            
            # Parse URL and update query parameter
            parsed = urlparse(current_url)
            query_params = parse_qs(parsed.query)
            query_params[param_name] = [str(page_num)]
            
            # Rebuild URL
            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            
            return new_url
        
        # Other pagination types would be handled here
        return None
    
    def _scrape_product_links(self, url: str) -> List[str]:
        """
        Scrape product links from a listing page.
        
        Args:
            url: Listing page URL
            
        Returns:
            List of product URLs
        """
        try:
            logger.info(f"Scraping listing page: {url}")
            response = self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            selector = self.config['selectors']['product_links']
            
            links = []
            for elem in soup.select(selector):
                href = elem.get('href')
                if href:
                    # Make absolute URL
                    absolute_url = urljoin(url, href)
                    links.append(absolute_url)
            
            logger.info(f"Found {len(links)} product links")
            return links
            
        except Exception as e:
            logger.error(f"Error scraping listing page {url}: {e}")
            self.errors.append({'url': url, 'error': str(e), 'type': 'listing'})
            return []
    
    def _scrape_product_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape product details from a product page.
        
        Args:
            url: Product page URL
            
        Returns:
            Product data dictionary or None if failed
        """
        try:
            logger.info(f"Scraping product: {url}")
            self._rate_limit()
            
            response = self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            detail_selectors = self.config['selectors']['product_detail']
            extraction_opts = self.config.get('extraction', {})
            
            # Initialize product data
            product = {
                'id': self._generate_product_id(url),
                'product_url': url,
                'category': self.config['category'],
            }
            
            # Extract basic fields
            for field in ['name', 'description', 'brand', 'sub_category']:
                if field in detail_selectors:
                    value = self._extract_text(soup, detail_selectors[field])
                    if extraction_opts.get('clean_text', True):
                        value = self._clean_text(value)
                    product[field] = value
            
            # Extract price
            if 'price' in detail_selectors:
                price_text = self._extract_text(soup, detail_selectors['price'])
                if extraction_opts.get('parse_price', True):
                    product['price'] = self._parse_price(price_text)
                else:
                    product['price'] = self._clean_text(price_text)
            
            # Extract currency
            if 'currency' in detail_selectors:
                product['currency'] = self._extract_text(soup, detail_selectors['currency'])
            else:
                product['currency'] = extraction_opts.get('default_currency', 'INR')
            
            # Extract attributes
            if 'attributes' in detail_selectors:
                attributes = {}
                for attr_name, attr_selector in detail_selectors['attributes'].items():
                    value = self._extract_text(soup, attr_selector)
                    if value:
                        attributes[attr_name] = self._clean_text(value)
                product['attributes'] = attributes
            
            # Extract features
            if 'features' in detail_selectors:
                features = self._extract_text(soup, detail_selectors['features'], extract_all=True)
                product['features'] = features if features else []
            
            # Extract images
            if 'image_url' in detail_selectors:
                image_url = self._extract_text(soup, detail_selectors['image_url'])
                if image_url:
                    product['image_url'] = urljoin(url, image_url)
            
            if extraction_opts.get('extract_all_images', False) and 'image_urls_all' in detail_selectors:
                image_urls = self._extract_text(soup, detail_selectors['image_urls_all'], extract_all=True)
                product['image_urls_all'] = [urljoin(url, img) for img in image_urls] if image_urls else []
            
            return product
            
        except Exception as e:
            logger.error(f"Error scraping product {url}: {e}")
            self.errors.append({'url': url, 'error': str(e), 'type': 'product'})
            return None
    
    def _generate_product_id(self, url: str) -> str:
        """Generate a unique product ID from URL."""
        # Extract last part of path or use hash
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if path_parts:
            # Use last meaningful part of URL
            product_id = path_parts[-1]
            # Clean it up
            product_id = re.sub(r'[^\w-]', '_', product_id)
            return product_id
        
        # Fallback to hash
        return str(hash(url))
    
    def scrape(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Run the scraping process.
        
        Args:
            limit: Maximum number of products to scrape
            
        Returns:
            List of product dictionaries
        """
        logger.info(f"Starting scrape of {self.config['site_name']} ({self.config['category']})")
        logger.info(f"Target: {limit} products")
        
        all_product_urls = set()
        
        # Scrape listing pages
        for start_url in self.config['start_urls']:
            current_url = start_url
            page_num = 1
            
            while current_url and len(all_product_urls) < limit:
                product_links = self._scrape_product_links(current_url)
                all_product_urls.update(product_links)
                
                logger.info(f"Total unique products found: {len(all_product_urls)}")
                
                # Get next page
                page_num += 1
                current_url = self._get_next_page_url(start_url, page_num)
                
                if current_url:
                    self._rate_limit()
        
        # Limit to requested number
        product_urls_to_scrape = list(all_product_urls)[:limit]
        logger.info(f"Scraping {len(product_urls_to_scrape)} product pages")
        
        # Scrape individual products
        for url in product_urls_to_scrape:
            product_data = self._scrape_product_detail(url)
            
            if product_data:
                self.products.append(product_data)
            
            # Check if we should skip on error
            elif not self.config.get('error_handling', {}).get('skip_on_error', True):
                logger.error("Stopping due to error (skip_on_error=False)")
                break
        
        logger.info(f"Scraping complete! Collected {len(self.products)} products")
        
        if self.errors:
            logger.warning(f"Encountered {len(self.errors)} errors during scraping")
        
        return self.products
    
    def get_results(self) -> Dict[str, Any]:
        """Get scraping results including products and metadata."""
        return {
            'site_name': self.config['site_name'],
            'category': self.config['category'],
            'total_products': len(self.products),
            'total_errors': len(self.errors),
            'products': self.products,
            'errors': self.errors if self.config.get('error_handling', {}).get('log_errors', True) else []
        }
    
    def close(self):
        """Close HTTP client."""
        self.client.close()


def scrape_products(config_path: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Convenience function to scrape products.
    
    Args:
        config_path: Path to YAML configuration file
        limit: Maximum number of products to scrape
    
    Returns:
        List of product dictionaries
    """
    scraper = ProductScraper(config_path)
    try:
        products = scraper.scrape(limit=limit)
        return products
    finally:
        scraper.close()
