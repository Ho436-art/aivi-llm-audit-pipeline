import urllib.request

url = "https://campus.aivilabs.com/assets/ResumeIntelligence-Cu50A2_q.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
print(f"ResumeIntelligence length: {len(data)}")

# Search for cloud function call or scoring logic
terms = ['httpsCallable', 'analyze', 'evaluate', 'prompt', 'score', 'scoreAES', 'gemini', 'gpt']
for t in terms:
    idx = 0
    while True:
        pos = data.lower().find(t.lower(), idx)
        if pos == -1:
            break
        print(f"Found '{t}' at {pos}:")
        start = max(0, pos - 80)
        end = min(len(data), pos + 120)
        print(" ", data[start:end])
        idx = pos + len(t) + 50
        if idx > pos + 300: # Limit matches per term
            break
