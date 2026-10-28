import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

styles = re.findall(r'<([a-zA-Z0-9\-]+)[^>]*\sstyle=["\']([^"\']+)["\'][^>]*>', text)
print(f"Total elements with inline style: {len(styles)}")
for tag, style in styles:
    if 'display:none' not in style.replace(' ', ''):
        print(f"<{tag}> inline style: {style}")
