f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
lines = f.readlines()
f.close()

# Print addToOcrQueue and processNext functions
printing = False
count = 0
for i, line in enumerate(lines):
    if "function addToOcrQueue" in line or "async function processNext" in line or "function finishOcr()" in line:
        printing = True
        count = 0
    if printing:
        print(f"{i+1}: {lines[i].rstrip()}")
        count += 1
        if count > 60:
            printing = False
            print("...")
