import urllib.request
import re

url = "https://campus.aivilabs.com/assets/index-BsiDyhP2.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
content = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

# Find all chunk imports
chunks = re.findall(r'import\(\`\.\/([a-zA-Z0-9_-]+\.js)\`\)', content)
print(f"Total chunks found: {len(chunks)}")

keywords = ['Resume', 'resume', 'JobFit', 'job-fit', 'Interview', 'interview', 'Student', 'student', 'Score', 'score', 'Parse', 'parse']
matched = [c for c in chunks if any(k.lower() in c.lower() for k in keywords)]
print(f"Matched chunks ({len(matched)}):")
for m in matched:
    print(" -", m)
