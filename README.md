# Shopify Checkout Analyzer

A tool to analyze Shopify store checkouts and determine if they use 1-Click Checkout (1CC) functionality.

## Prerequisites

- Python 3.7+
- Required Python packages (install using `pip install -r requirements.txt`)

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

To analyze a list of Shopify store URLs:

```bash
python main.py --input shopify_urls.csv --output results.csv
```

### Command Line Arguments

- `--input`, `-i`: Path to input CSV file containing Shopify store URLs (one per line)
- `--output`, `-o`: Path to output CSV file (default: `results.csv`)
- `--urls`: Space-separated list of URLs to process (alternative to input file)
- `--batch-size`: Number of URLs to process in each batch (default: 50)
- `--workers`: Number of concurrent workers (default: 10)
- `--state`: State for shipping address (default: Karnataka)

### Input File Format

Create a CSV file (`shopify_urls.csv`) with the following format:

```
url
https://example-store1.com
https://example-store2.com
```

### Output

The tool generates a CSV file with the following columns:
- `website`: The store URL that was analyzed
- `platform`: Detected platform (e.g., 'shopify')
- `one_cc`: Boolean indicating if 1-Click Checkout is detected
- `product_names`: Names of products found (first 5)
- `variant_id`: ID of the product variant used for checkout
- `checkout_url`: Generated checkout URL
- `status`: Status of the analysis
- `error`: Any error messages if the analysis failed

## How It Works

1. The tool reads a list of Shopify store URLs
2. For each URL, it:
   - Identifies if it's a Shopify store
   - Attempts to fetch product information
   - Builds a checkout URL with a test product
   - Determines if 1-Click Checkout is enabled

## Configuration

Modify `constants.py` to adjust:
- Timeouts
- Retry attempts
- User agent strings
- Referrer headers

## Logging

The tool logs detailed information to `checkout_analyzer.log` in the same directory.

## Troubleshooting

- If you encounter rate limiting, try reducing the number of workers
- Ensure all URLs in the input file are valid Shopify store URLs
- Check the log file for detailed error messages

## License

This tool is proprietary software. Unauthorized use, reproduction, or distribution is strictly prohibited.
