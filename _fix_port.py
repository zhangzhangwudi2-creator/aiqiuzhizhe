f = open("main.py", "r", encoding="utf-8")
c = f.read()
f.close()

# Replace the if __name__ block to support PORT env var
old = """if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)"""

new = """if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)"""

c = c.replace(old, new)

# Also update the uvicorn.run reference since we use main:app
c = c.replace('uvicorn.run("backend.main:app"', 'uvicorn.run("main:app"')

f = open("main.py", "w", encoding="utf-8")
f.write(c)
f.close()
print("Updated for PORT env var")
