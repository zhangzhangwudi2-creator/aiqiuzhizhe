f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

# Find the JD card section
i = c.find('class="upload-zone ocr-zone"')
if i >= 0:
    print("=== OCR Zone HTML ===")
    # Print surrounding HTML
    start = c.rfind("<", i-200)
    end = c.find(">", i+300)
    print(c[start:end+1])
else:
    print("OCR zone NOT FOUND")
    # Check what's around the JD card
    j = c.find('ocr-divider')
    if j >= 0:
        print("ocr-divider found at", j)
        print(c[j:j+500])
    else:
        print("ocr-divider also not found")
