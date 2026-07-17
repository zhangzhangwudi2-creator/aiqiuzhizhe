f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

# Check if there is </script> inside a JavaScript string
# (which would break the HTML parsing)
import re
# Find all places where </script> appears but is not an actual tag closing
# These would be inside JS strings
matches = list(re.finditer(r"<(?!/)script>", c, re.IGNORECASE))
print("Total script-related patterns:")
for m in re.finditer(r"script>", c):
    ctx = c[max(0,m.start()-50):m.end()+10]
    print(f"  pos {m.start()}: ...{ctx}...")
