import urllib.request

url = "https://campus.aivilabs.com/assets/UpgradeModal-Bad7ayuU.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

idx = data.find('Backend call failed, using dynamic local engine')
if idx != -1:
    start = max(0, idx - 400)
    end = min(len(data), idx + 2000)
    print("=== DYNAMIC LOCAL ENGINE & BACKEND CALL ===")
    print(data[start:end])
