f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

# Find the extra </script>
count = 0
for i, ch in enumerate(c):
    if c[i:i+9] == "</script>":
        count += 1
        if count == 2:
            print(f"Extra </script> at position {i}")
            print(f"Context: {c[max(0,i-100):i+50]}")
            break

# Also find the <script> positions
print("\n<script> positions:")
for i, ch in enumerate(c):
    if c[i:i+8] == "<script>":
        print(f"  at {i}: {c[max(0,i-20):i+50]}")
