import urllib.request
import re

url = "https://campus.aivilabs.com/assets/ResumeIntelligence-Cu50A2_q.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

# Check top 5 imports of ResumeIntelligence
for line in data[:1000].split(';'):
    if 'import' in line:
        print(line.strip())

# Check usage of d(...)
print("\nUsages of d(...):")
for m in re.finditer(r'([^;{}]{0,50}\bd\([^)]+\)[^;{}]{0,50})', data):
    print(" ", m.group(0))
