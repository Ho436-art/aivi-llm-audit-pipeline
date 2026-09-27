import urllib.request
import re

url = "https://campus.aivilabs.com/assets/UpgradeModal-Bad7ayuU.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
print(f"UpgradeModal length: {len(data)}")

# Search for export of c or definition of c
matches = re.findall(r'([a-zA-Z0-9_$]+)\s+as\s+c\b', data)
print("Mapped as c:", matches)

# Search for functions in UpgradeModal
print("Sample of UpgradeModal:")
for line in data.split(';'):
    if any(k in line for k in ['analysis_type', 'analyze', 'httpsCallable', 'fetch', 'api', 'result']):
        print(" ", line[:150])
