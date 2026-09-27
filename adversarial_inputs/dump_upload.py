import urllib.request

url = "https://campus.aivilabs.com/assets/ResumeUploadForm-5K9h0dmU.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
print("=== ResumeUploadForm ===")
print(data)
