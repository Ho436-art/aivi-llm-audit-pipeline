import urllib.request
import re

url = "https://campus.aivilabs.com/assets/ResumeIntelligence-Cu50A2_q.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

# Search for definition of Y
idx = data.find('Y=')
if idx != -1:
    print("Found Y=:")
    print(data[idx:idx+600])
else:
    print("Y= not found directly, searching for onAnalyze")
    for m in re.finditer(r'onAnalyze[:=]([a-zA-Z0-9_$]+)', data):
        print(m.group(0))
