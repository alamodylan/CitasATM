import requests
import time

url = "https://citasatm-1.onrender.com"
while True:
    try:
        response = requests.get(url)
        print(f"Pinged {url}, status code: {response.status_code}")
    except Exception as e:
        print(f"Error pinging {url}: {e}")
    time.sleep(600)  # Cada 10 minutos