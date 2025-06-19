import csv
import os
from urllib.parse import urlparse

def read_csv_file(path, url_list=None):
    """
    Read URLs from either a CSV file or a list of URLs.
    If both are provided, the list takes precedence.
    """
    if url_list and isinstance(url_list, list):
        return [ensure_https(url.strip()) for url in url_list if url.strip()]
        
    websites = []
    try:
        with open(path, 'r') as file:
            csv_reader = csv.reader(file)
            # Skip the header row if it exists
            try:
                next(csv_reader)
            except StopIteration:
                pass  # Empty file
                
            # Read each row and append the website value to the list
            for row in csv_reader:
                if not row or not row[0].strip():
                    continue
                website = row[0].strip()
                website = ensure_https(website)
                websites.append(website)
    except FileNotFoundError:
        print(f"File not found at path: {path}")
    
    return websites

def ensure_https(url):
    # Parse the URL
    parsed_url = urlparse(url)

    # Check if the scheme is already HTTPS
    if parsed_url.scheme == 'https':
        if not url.endswith("/"):
            url = url + "/"
        return url  # No modification needed

    # If not HTTPS, construct a new URL with HTTPS scheme
    https_url = f'https://{parsed_url.netloc}{parsed_url.path}'
    if parsed_url.query:
        https_url += f'?{parsed_url.query}'
    if parsed_url.fragment:
        https_url += f'#{parsed_url.fragment}'

    if not https_url.endswith("/"):
        https_url = https_url + "/"
    return https_url

def write_csv(data, csv_file, mode='w'):
    """
    Write data to a CSV file.
    
    Args:
        data: List of dictionaries containing the data to write
        csv_file: Path to the output CSV file
        mode: File write mode ('w' for write, 'a' for append)
    """
    fieldnames = [
        'website',
        'platform',
        'one_cc',
        'product_names',
        'variant_id',
        'checkout_url',
        'status',
        'error'
    ]
    
    # Ensure all dictionaries have the same fields
    for row in data:
        for field in fieldnames:
            row.setdefault(field, '')
    
    file_exists = os.path.isfile(csv_file) and os.path.getsize(csv_file) > 0
    
    with open(csv_file, mode, newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write header only if file doesn't exist or we're in write mode
        if not file_exists or mode == 'w':
            writer.writeheader()
            
        # Write the data
        for row in data:
            writer.writerow(row)
