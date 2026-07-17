f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "r", encoding="utf-8-sig")
c = f.read()
f.close()

old = 'async def download_rewrite'
idx = c.find(old)
if idx >= 0:
    next_func = c.find('@app.get("/health")', idx)
    if next_func > 0:
        c = c[:idx-7] + c[next_func:]
        print("Removed download-rewrite endpoint")
f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "w", encoding="utf-8")
f.write(c)
f.close()
