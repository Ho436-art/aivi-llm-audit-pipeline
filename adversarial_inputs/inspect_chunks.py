import urllib.request

for chunk in ['ResumeIntelligence-Cu50A2_q.js', 'JobFitAnalysis-CtN1KSre.js']:
    url = f"https://campus.aivilabs.com/assets/{chunk}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
        print(f"\n=== {chunk} (length {len(data)}) ===")
        # Search for key terms
        terms = ['pdf', 'upload', 'ocr', 'score', 'scoreAES', 'employability', 'extract', 'gemini', 'openai', 'claude', 'prompt', 'AES', 'vision']
        found = [t for t in terms if t.lower() in data.lower()]
        print("Found keywords:", found)
        # Look for upload or scoring snippets
        for line in data.split(';'):
            if any(k in line.lower() for k in ['employability', 'score', 'upload', 'ocr', 'pdf']):
                if 20 < len(line) < 300:
                    print("  Snippet:", line.strip())
                    break
    except Exception as e:
        print(f"Error fetching {chunk}: {e}")
