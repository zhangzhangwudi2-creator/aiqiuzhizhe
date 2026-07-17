f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

# Find all function declarations in the main script
i = c.find("<script>\n// === Resume")
j = c.find("</script>", i)
script = c[i:j]

import re
funcs = re.findall(r"(async\s+)?function\s+(\w+)\s*\(", script)
print("Functions in order:")
for is_async, name in funcs:
    print(f"  {'async ' if is_async else ''}function {name}()")
