f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

# Check if these key elements exist
for term in ['ocr-zone', 'ocr-divider', 'jdImageZone', 'jdImageInput', 'ocrProgress']:
    idx = c.find(term)
    print(f"{term}: {idx}")

# Show the area around the JD textarea
i = c.find('id="jdInput"')
if i >= 0:
    end = c.find('</div>', i)
    end = c.find('</div>', end+6)
    print("\n=== JD Input area ===")
    print(c[i-100:end+10])
