import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate"
}

url = "https://boutiquedesartsmartiaux.com/sitemap_products_1.xml?from=7943275774171&to=7958964666587"
response = requests.get(url, headers=headers)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(response.text[:500])  # Vérifie si c'est bien du XML
