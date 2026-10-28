import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

cards = re.findall(r'<div[^>]*class=["\'][^"\']*modal-card[^"\']*["\'][^>]*>', text)
print(f"Total modal-cards: {len(cards)}")
for c in cards:
    id_m = re.search(r'id=["\']([^"\']+)["\']', c)
    cls_m = re.search(r'class=["\']([^"\']+)["\']', c)
    style_m = re.search(r'style=["\']([^"\']+)["\']', c)
    print(f"Card ID: {id_m.group(1) if id_m else 'NO-ID'} | Class: {cls_m.group(1) if cls_m else 'NO-CLASS'}")
    if style_m:
        print(f"   Inline style: {style_m.group(1)}")
