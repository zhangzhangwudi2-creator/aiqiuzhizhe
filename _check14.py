f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

positions = []
start = 0
while True:
    idx = c.find("</script>", start)
    if idx < 0: break
    positions.append(idx)
    start = idx + 1

print(f"Found {len(positions)} </script> tags:")
for i, pos in enumerate(positions):
    print(f"  #{i+1}: pos {pos}, context: ...{c[max(0,pos-30):pos+30]}...")
