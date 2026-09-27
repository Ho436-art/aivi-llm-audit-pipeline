import urllib.request
import re

url = "https://campus.aivilabs.com/assets/ResumeUploadForm-5K9h0dmU.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
print(f"Length: {len(data)}")

# Search for upload constraints, accepted types, api calls
print("Accepted file types:")
for m in re.finditer(r'accept[:=]\s*["\']([^"\']+)["\']', data, re.I):
    print(" ", m.group(0))

# Search for function calls or fetch/post
print("Calls/Endpoints:")
for m in re.finditer(r'(https?://[^\s"\']+|/api/[^\s"\']+|callable[^\s"\']+|parse[a-zA-Z0-9]+)', data):
    print(" ", m.group(0))
