import urllib.request

url = "https://campus.aivilabs.com/assets/UpgradeModal-Bad7ayuU.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

# Locate function w
idx = data.find('function w(')
if idx != -1:
    print("Found function w(:")
    print(data[idx:idx+1000])
else:
    for m in ['var w=', 'let w=', 'const w=']:
        idx = data.find(m)
        if idx != -1:
            print(f"Found {m}:")
            print(data[idx:idx+1000])
            break
