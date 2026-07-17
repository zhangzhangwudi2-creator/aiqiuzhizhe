f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

i = c.find('id="jdImageZone"')
print("jdImageZone to end of card:")
end = c.find('</div>\n      </div>\n\n    <div class="btn-wrapper"', i)
print(c[i:end+10])
