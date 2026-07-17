f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
lines = f.readlines()
f.close()

# Print lines around the OCR JS
for i, line in enumerate(lines):
    if "jdImageZone.addEventListener" in line:
        for j in range(max(0,i-1), min(len(lines), i+4)):
            print(f"{j+1}: {lines[j].rstrip()}")
        print("---")
    if "jdImageInput.addEventListener" in line:
        for j in range(max(0,i-1), min(len(lines), i+4)):
            print(f"{j+1}: {lines[j].rstrip()}")
        print("---")
