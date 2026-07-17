f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "r", encoding="utf-8")
c = f.read()
f.close()

# Add cache-control headers to the index endpoint
old = """@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()"""

new = """@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    from fastapi.responses import Response
    return Response(content=content, media_type="text/html", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})"""

c = c.replace(old, new)

f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "w", encoding="utf-8")
f.write(c)
f.close()
print("Cache headers added")
