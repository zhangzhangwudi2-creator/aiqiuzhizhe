f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

i = c.find('id="jdImageZone"')
# Find the closing div for jdImageZone - look for the pattern after its content
# The zone closes when we hit the next sibling element or the parent's closing
for j in range(i, min(i+800, len(c))):
    pass
print("From jdImageZone to +500 chars:")
print(c[i:i+500])
