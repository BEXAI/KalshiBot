import os, certifi, time, base64, aiohttp, asyncio
os.environ['SSL_CERT_FILE'] = certifi.where()
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from settings import settings

async def test():
    with open(settings.KALSHI_PRIVATE_KEY_PATH, 'rb') as f:
        private_key = load_pem_private_key(f.read(), password=None)

    method = 'GET'
    path = '/portfolio/balance'
    api_path = '/trade-api/v2'
    # Let's try to sign with the full path
    full_path = api_path + path
    timestamp = str(int(time.time() * 1000))
    msg_string = timestamp + method + full_path
    
    signature = private_key.sign(
        msg_string.encode('utf-8'),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    encoded_sig = base64.b64encode(signature).decode('utf-8')
    headers = {
        'KALSHI-ACCESS-KEY': settings.KALSHI_API_KEY_ID,
        'KALSHI-ACCESS-SIGNATURE': encoded_sig,
        'KALSHI-ACCESS-TIMESTAMP': timestamp,
        'Content-Type': 'application/json'
    }
    url = 'https://api.elections.kalshi.com' + full_path
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print("Status:", resp.status)
            print("Resp:", await resp.json())

asyncio.run(test())
