import os
import time
import json
import argparse
import logging
from datetime import datetime
from concurrent import futures
import scraper
import storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('checkout_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process Shopify store URLs for checkout analysis.')
    parser.add_argument('--input', '-i', type=str, help='Path to input CSV file containing URLs')
    parser.add_argument('--output', '-o', type=str, default='checkout_analysis_results.csv',
                       help='Path to output CSV file (default: checkout_analysis_results.csv)')
    parser.add_argument('--urls', type=str, nargs='+', help='List of URLs to process (space-separated)')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Number of URLs to process in each batch (default: 50)')
    parser.add_argument('--workers', type=int, default=10,
                       help='Number of concurrent workers (default: 10)')
    parser.add_argument('--state', type=str, default='Karnataka',
                       help='State for shipping address (default: Karnataka)')
    return parser.parse_args()

def process_website(website, state):
    """Process a single website and return the result."""
    try:
        logger.info(f"Processing: {website}")
        
        # Get platform and 1CC status
        platform, onecc = scraper.get_platform(website)
        result = {
            'website': website,
            'platform': platform,
            'one_cc': onecc,
            'product_names': '',
            'variant_id': '',
            'checkout_url': '',
            'status': 'success',
            'error': ''
        }
        
        # Skip if not Shopify or defunct
        if platform != 'Shopify' or platform == 'defunct':
            result['status'] = 'skipped'
            return result
        
        # Get product information
        response = scraper.get_products(website)
        if not response:
            result['status'] = 'failed'
            result['error'] = 'No products found or failed to fetch products'
            return result
            
        # Extract product details
        product_names = response.get("product_names", "")
        variant_id = response.get("variant_id", "")
        
        # Build checkout URL
        checkout_url = ""
        if variant_id:
            checkout_url = scraper.build_checkout_url(website, variant_id, state)
        
        # Update result
        result.update({
            'product_names': product_names,
            'variant_id': variant_id,
            'checkout_url': checkout_url
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing {website}: {str(e)}")
        return {
            'website': website,
            'platform': '',
            'one_cc': '',
            'product_names': '',
            'variant_id': '',
            'checkout_url': '',
            'status': 'error',
            'error': str(e)
        }

def process_batch(websites, state, batch_num, total_batches, output_file):
    """Process a batch of websites and save results."""
    results = []
    logger.info(f"Starting batch {batch_num + 1} of {total_batches} with {len(websites)} URLs")
    
    for i, website in enumerate(websites, 1):
        logger.info(f"Processing URL {i}/{len(websites)} in batch {batch_num + 1}")
        result = process_website(website, state)
        results.append(result)
        
        # Save progress after each URL
        storage.write_csv([result], output_file, mode='a' if batch_num > 0 or i > 1 else 'w')
    
    return results

def main():
    args = parse_arguments()
    
    # Read URLs from file or command line
    if args.urls:
        websites = storage.read_csv_file(None, url_list=args.urls)
    elif args.input:
        websites = storage.read_csv_file(args.input)
    else:
        logger.error("No input source provided. Use --input or --urls")
        return
    
    if not websites:
        logger.error("No valid URLs found in the input source")
        return
    
    logger.info(f"Starting analysis of {len(websites)} URLs")
    
    # Split into batches
    batch_size = min(args.batch_size, len(websites))
    batches = [websites[i:i + batch_size] for i in range(0, len(websites), batch_size)]
    
    # Process batches sequentially but URLs within batches in parallel
    with futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_batch = {}
        
        for i, batch in enumerate(batches):
            # Process each URL in the batch in parallel
            future = executor.submit(
                process_batch, 
                batch, 
                args.state, 
                i, 
                len(batches),
                args.output
            )
            future_to_batch[future] = i
        
        # Wait for all batches to complete
        for future in futures.as_completed(future_to_batch):
            batch_num = future_to_batch[future]
            try:
                results = future.result()
                success_count = sum(1 for r in results if r.get('status') == 'success')
                logger.info(f"Batch {batch_num + 1} completed: {success_count}/{len(results)} successful")
            except Exception as e:
                logger.error(f"Error in batch {batch_num + 1}: {str(e)}")
    
    logger.info(f"Analysis complete. Results saved to {args.output}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    logger.info(f"Total execution time: {(time.time() - start_time):.2f} seconds")

