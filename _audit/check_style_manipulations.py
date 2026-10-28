import re

with open('frontend/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

style_writes = re.findall(r'(\b\w+)\.style\.([a-zA-Z]+)\s*=', text)
print(f"Total style properties written in app.js: {len(style_writes)}")
written_props = {}
for var, prop in style_writes:
    written_props[prop] = written_props.get(prop, 0) + 1

for prop, count in sorted(written_props.items(), key=lambda x: -x[1]):
    print(f"  .style.{prop}: {count} times")

print("\nSpecific lines manipulating style:")
lines = text.split('\n')
for i, line in enumerate(lines):
    if '.style.background' in line or '.style.color' in line or '.style.border' in line:
        print(f"Line {i+1}: {line.strip()}")
