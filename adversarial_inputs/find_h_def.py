import urllib.request
import re

url = "https://campus.aivilabs.com/assets/index-BsiDyhP2.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

# Search for export of H or definition of H
# In Vite/Rollup bundles: export { ... Ht as H ... }
matches = re.findall(r'([a-zA-Z0-9_$]+)\s+as\s+H\b', data)
print("Mapped as H:", matches)

if matches:
    name = matches[0]
    idx = data.find(f"{name}=")
    if idx == -1:
        idx = data.find(f"function {name}")
    print(f"Definition of {name}:")
    print(data[idx:idx+600])
