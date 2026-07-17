f = open("C:/Users/张凡/Documents/ai求职助手 2/static/index.html", "r", encoding="utf-8")
c = f.read()
f.close()

# Check for potential issues
issues = []
if "function escHtml" in c:
    # Count occurrences
    count = c.count("function escHtml")
    if count > 1: issues.append(f"DUPLICATE escHtml ({count}x)")
    
# Check for unclosed tags in the OCR area
i = c.find("jdImageZone")
section = c[i:i+1000]
open_divs = section.count("<div")
close_divs = section.count("</div")
print(f"jdImageZone section: {open_divs} open divs, {close_divs} close divs")
if open_divs != close_divs:
    issues.append(f"MISMATCHED divs in OCR zone: {open_divs} open vs {close_divs} close")

# Check script tags
open_script = c.count("<script>")
close_script = c.count("</script>")
print(f"Script tags: {open_script} open, {close_script} close")
if open_script != close_script:
    issues.append(f"MISMATCHED script tags")

print("\nIssues found:", issues if issues else "NONE")
