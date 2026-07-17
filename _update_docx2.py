import re

f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "r", encoding="utf-8")
c = f.read()
f.close()

# Find the old doc generation block
old_marker = '# \u751f\u6210 Word \u6587\u6863'
idx = c.find(old_marker)
if idx < 0:
    # Try without comment
    idx = c.find("doc = Document()")
print(f"Found doc generation at {idx}")

# Find the end of the download-rewrite function
end_marker = "return StreamingResponse("
end_idx = c.find(end_marker, idx)

# The new doc generation code
new_code = """    # Generate Word document
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(10.5)
    style.paragraph_format.space_after = Pt(4)
    style.paragraph_format.line_spacing = 1.3
    style.font.color.rgb = RGBColor(0, 0, 0)

    for level in range(1, 4):
        hs = doc.styles[f"Heading {level}"]
        hs.font.color.rgb = RGBColor(0, 0, 0)
        hs.font.name = "Arial"

    def clean(text):
        text = re.sub(r'\\*\\*(.+?)\\*\\*', r'\\1', text)
        text = re.sub(r'\\*(.+?)\\*', r'\\1', text)
        text = re.sub(r'__(.+?)__', r'\\1', text)
        text = re.sub(r'_([^_]+?)_', r'\\1', text)
        text = re.sub(r'`(.+?)`', r'\\1', text)
        text = re.sub(r'\\[(.+?)\\]\\(.+?\\)', r'\\1', text)
        text = re.sub(r'~~~+', '', text)
        text = re.sub(r'```', '', text)
        return text

    for line in md_text.split("\\n"):
        ls = line.strip()
        if not ls:
            doc.add_paragraph("")
        elif ls.startswith("### "):
            doc.add_heading(clean(ls[4:]), level=3)
        elif ls.startswith("## "):
            doc.add_heading(clean(ls[3:]), level=2)
        elif ls.startswith("# "):
            doc.add_heading(clean(ls[2:]), level=1)
        elif ls.startswith("- ") or ls.startswith("* "):
            doc.add_paragraph(clean(ls[2:]), style="List Bullet")
        elif re.match(r'^\\d+\\.\\s', ls):
            num_content = re.sub(r'^\\d+\\.\\s', '', ls)
            doc.add_paragraph(clean(num_content), style="List Number")
        else:
            doc.add_paragraph(clean(ls))

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)"""

# Find what to replace
# From "doc = Document()" to "buf = io.BytesIO()"
old_start = c.find("doc = Document()", idx)
old_end = c.find("buf = io.BytesIO()", old_start)

print(f"Replacing from {old_start} to {old_end}")
print(f"Old code snippet: {c[old_start:min(old_start+200, old_end)]}")

c = c[:old_start] + new_code + c[old_end:]

f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "w", encoding="utf-8")
f.write(c)
f.close()
print("Done")
