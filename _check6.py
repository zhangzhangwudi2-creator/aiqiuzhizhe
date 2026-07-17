f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

i = c.find('id="jdImageZone"')
if i >= 0:
    end = c.find('</div>', i)
    end = c.find('</div>', end+6)  # close the ocr-zone div
    print("Full OCR zone HTML:")
    print(c[i:end+10])
