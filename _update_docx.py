f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "r", encoding="utf-8")
c = f.read()
f.close()

# Find the download-rewrite function and replace the doc generation part
old_doc = """    # 生成 Word 文档
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.font.size = Pt(10.5)
    style.paragraph_format.space_after = Pt(4)
    style.paragraph_format.line_spacing = 1.3

    for line in md_text.split("\\n"):
        line_stripped = line.strip()
        if not line_stripped:
            doc.add_paragraph("")
        elif line_stripped.startswith("# "):
            h = doc.add_heading(line_stripped[2:], level=1)
        elif line_stripped.startswith("## "):
            h = doc.add_heading(line_stripped[3:], level=2)
        elif line_stripped.startswith("### "):
            h = doc.add_heading(line_stripped[4:], level=3)
        elif line_stripped.startswith("- "):
            doc.add_paragraph(line_stripped[2:], style="List Bullet")
        elif line_stripped.startswith("**") and line_stripped.endswith("**"):
            p = doc.add_paragraph()
            run = p.add_run(line_stripped.strip("*"))
            run.bold = True
        else:
            doc.add_paragraph(line_stripped)"""

new_doc = """    # 生成 Word 文档
    doc = Document()
    
    # 设置默认样式
    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.font.size = Pt(10.5)
    style.paragraph_format.space_after = Pt(4)
    style.paragraph_format.line_spacing = 1.3
    style.font.color.rgb = RGBColor(0, 0, 0)
    
    # 修改标题样式 - 去掉默认蓝色
    for level in range(1, 4):
        hs = doc.styles[f"Heading {level}"]
        hs.font.color.rgb = RGBColor(0, 0, 0)
        hs.font.name = "微软雅黑"

    import re
    
    def strip_markdown(text):
        """去除 markdown 标记，返回纯文本"""
        # 去除加粗/斜体标记
        text = re.sub(r'\\*\\*(.+?)\\*\\*', r'\\1', text)
        text = re.sub(r'\\*(.+?)\\*', r'\\1', text)
        text = re.sub(r'__(.+?)__', r'\\1', text)
        text = re.sub(r'_(.+?)_', r'\\1', text)
        # 去除行内代码标记
        text = re.sub(r'`(.+?)`', r'\\1', text)
        # 去除链接标记 [text](url)
        text = re.sub(r'\\[(.+?)\\]\\(.+?\\)', r'\\1', text)
        return text
    
    for line in md_text.split("\\n"):
        ls = line.strip()
        if not ls:
            doc.add_paragraph("")
        elif ls.startswith("#### "):
            p = doc.add_paragraph()
            run = p.add_run(strip_markdown(ls[5:]))
            run.bold = True
            run.font.size = Pt(10.5)
        elif ls.startswith("### "):
            h = doc.add_heading(strip_markdown(ls[4:]), level=3)
        elif ls.startswith("## "):
            h = doc.add_heading(strip_markdown(ls[3:]), level=2)
        elif ls.startswith("# "):
            h = doc.add_heading(strip_markdown(ls[2:]), level=1)
        elif ls.startswith("- ") or ls.startswith("* "):
            doc.add_paragraph(strip_markdown(ls[2:]), style="List Bullet")
        elif ls.startswith("1. ") or ls.startswith("2. ") or ls.startswith("3. "):
            doc.add_paragraph(strip_markdown(ls[3:]), style="List Number")
        else:
            doc.add_paragraph(strip_markdown(ls))"""

c = c.replace(old_doc, new_doc)

f = open("C:/Users/张凡/Documents/ai求职助手 2/main.py", "w", encoding="utf-8")
f.write(c)
f.close()
print("DOCX generation updated with markdown stripping")
