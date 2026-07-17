f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

i = c.find('id="jdImageZone"')
btn_idx = c.find('btn-wrapper', i)
if btn_idx > 0:
    print("jdImageZone to btn-wrapper:")
    print(c[i:btn_idx])
else:
    print("btn-wrapper not found after jdImageZone")
    # Try different patterns
    for term in ['ocr-status', 'card-label', 'btn-analyze']:
        idx = c.find(term, i)
        if idx > 0:
            print(f"{term} at {idx}")
