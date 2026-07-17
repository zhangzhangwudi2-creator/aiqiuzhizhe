f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "r", encoding="utf-8-sig")
c = f.read()
f.close()
old = 'uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)'
new = 'uvicorn.run(app, host="0.0.0.0", port=port)'
c = c.replace(old, new)
f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "w", encoding="utf-8")
f.write(c)
f.close()
print("Fixed")
