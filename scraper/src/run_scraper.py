"""
CLI entry point for the product scraper.
Run with: python run_scraper.py --config config/watches_site_template.yaml --limit 100
"""

import argparse
import json
import sys
from pathlib import Path
from scraper_core import ProductScraper
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Config-driven e-commerce product scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape 100 watches
  python run_scraper.py --config config/watches_site_template.yaml --limit 100
  
  # Scrape 500 products with custom output
  python run_scraper.py --config config/watches_site_template.yaml --limit 500 --output custom_output.json
  
  # Verbose logging
  python run_scraper.py --config config/watches_site_template.yaml --limit 50 --verbose
        """
    )
    
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML configuration file"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of products to scrape (default: 100)"
    )
    
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: data/products_{category}.json)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load config and validate without scraping"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize scraper
        logger.info(f"Loading configuration from: {args.config}")
        scraper = ProductScraper(args.config)
        
        config_info = scraper.config
        logger.info(f"Site: {config_info['site_name']}")
        logger.info(f"Category: {config_info['category']}")
        logger.info(f"Start URLs: {len(config_info['start_urls'])}")
        
        if args.dry_run:
            logger.info("Dry run mode - configuration loaded successfully")
            logger.info(f"Config details: {json.dumps(config_info, indent=2)}")
            return 0
        
        # Run scraping
        logger.info(f"Starting scrape (limit: {args.limit} products)")
        products = scraper.scrape(limit=args.limit)
        
        # Get full results
        results = scraper.get_results()
        
        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            # Default: data/products_{category}.json
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            output_path = data_dir / f"products_{config_info['category']}.json"
        
        # Save results
        logger.info(f"Saving {len(products)} products to: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "=" * 60)
        print("SCRAPING COMPLETE")
        print("=" * 60)
        print(f"Site: {results['site_name']}")
        print(f"Category: {results['category']}")
        print(f"Products scraped: {results['total_products']}")
        print(f"Errors encountered: {results['total_errors']}")
        print(f"Output file: {output_path}")
        print("=" * 60)
        
        # Show sample product
        if products:
            print("\nSample product:")
            print(json.dumps(products[0], indent=2))
        
        return 0
        
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {args.config}")
        return 1
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        return 1
    finally:
        try:
            scraper.close()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
