import urllib.request

url = "https://campus.aivilabs.com/assets/UpgradeModal-Bad7ayuU.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

# Locate function T and D
for func_name in ['function T(', 'var T=', 'let T=', 'const T=']:
    idx = data.find(func_name)
    if idx != -1:
        print(f"Found {func_name} at {idx}:")
        print(data[idx:idx+1500])
        break

for func_name in ['function D(', 'var D=', 'let D=', 'const D=']:
    idx = data.find(func_name)
    if idx != -1:
        print(f"\nFound {func_name} at {idx}:")
        print(data[idx:idx+1500])
        break
