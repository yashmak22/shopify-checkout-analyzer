import requests
import time
import json
import constants
import random

user_agents = [
    # iPhone devices
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",

    # Android devices
    "Mozilla/5.0 (Linux; Android 11; SM-G988U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Mobile Safari/537.36",

    # Laptop/desktop devices
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36 Edg/94.0.992.47",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
]

# Define referrer headers for common advertising platforms
referrer_headers = [
    # Google Ads
    "https://www.google.com/",
    "https://www.googleadservices.com/",

    # Facebook Ads
    "https://www.facebook.com/",
    "https://l.facebook.com/",

    # Twitter Ads
    "https://twitter.com/",
    "https://t.co/",

    # LinkedIn Ads
    "https://www.linkedin.com/",
    "https://lnkd.in/",

    # Instagram Ads
    "https://www.instagram.com/",
    "https://l.instagram.com/"
]

# 402 is Shopify's code for a paused shop.
# 404 is if the website has some customizations which block the `/products.json` endpoint.
failed_status_codes = {401, 402, 403, 404, 423, 500, 501, 502, 503, 504, 521, 525}

# get_platform queries the html code and matches it to known CDN links
# to detect the underlying technologies used.
def get_platform(website):
  platform = "not_found"
  onecc = "none"
  html = poll_url(website)
  if html == "":
     return "defunct", onecc
  # we have the raw html, now do string comparisons.
  for keyword, output in constants.PlatformMap.items():
    if keyword in html:
        platform = output
        break
  # check for 1cc player CDN scripts
  for keyword, output in constants.CheckoutMap.items():
    if keyword in html:
        onecc = output
        break
  return platform, onecc

# poll_url makes GET requests to Shopify and handles retries and spoofing headers.
def poll_url(website):
  text = ""
  sleep_interval = 0.2 # second
  while text == "":
    try:
      response = make_request(website)
    except requests.RequestException as e:
      print(e)
      break
    print('status_code: ' + str(response.status_code))
    print('sleep_interval: ' + str(sleep_interval))
    if response.status_code == 200:
       text = response.text
       break
    # For defunct websites.
    if response.status_code in failed_status_codes:
       break
    # For any recoverable failures/ blocks.
    if sleep_interval > 32:
        break
    if sleep_interval == 0.3:
       sleep_interval = 1
    sleep_interval *= 2
    time.sleep(sleep_interval)
  return text


def get_products(website):
  # website has trailing `/`
  product_url = website + "products.json"
  data = poll_url(product_url)
  if data == "":
     return {}
  products = json.loads(data)
  products = products["products"]
  return {
     "variant_id": get_valid_variant(products),
     "product_names": concat_product_names(products) ,
  }

# make_request spoofs headers to make the requests look genuine and avoid being blocked.
def make_request(url):
   random_user_agent = random.choice(user_agents)
   referrer_header = random.choice(referrer_headers)
   custom_headers = {
    'User-Agent': random_user_agent,
    'Referer': referrer_header,
    'Accept-Language': 'en-US'
  }
   return requests.get(url, timeout=15, headers=custom_headers)

# build_checkout_url builds a cart permalink which can directly be opened by
# any headless browser such as Selenium with all the checkout details prefilled.
def build_checkout_url(url, variant_id, state):
   zip = constants.Locations[state]
   email = "john.doe@gmail.com"
   phone = "9920000000"
   return url + "cart/" +str(variant_id)+ ":1?" + "checkout[email]="+email+"&checkout[phone]="+phone+"&checkout[shipping_address][first_name]=John&checkout[shipping_address][last_name]=Doe&checkout[shipping_address][address1]=Arena Building&checkout[shipping_address][address2]&checkout[shipping_address][city]=Bangalore&checkout[shipping_address][province]="+state+"&checkout[shipping_address][country]=India&checkout[shipping_address][zip]="+zip+"&checkout[shipping_address][phone]="+phone

# concat_product_names combines the first 5 product names.
# This can be used to map the merchant to an MCC..
def concat_product_names(data):
   products = data
   if len(products) > 4:
         products = products[:5]
   names = ""
   for product in products:
      names = names + " " + product["handle"]
   return names

# get_valid_variant returns the first variant available to avoid issues like out-of-stock when using Selenium.
def get_valid_variant(products):
   for product in products:
      variants = product['variants']
      for variant in variants:
         if variant['available']:
            return variant['id']
   return ""