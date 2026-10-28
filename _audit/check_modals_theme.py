import re

with open('frontend/css/style.css', 'r', encoding='utf-8') as f:
    content = f.read()

modals = [
    'modal-invoice', 'modal-ai-notification', 'modal-qr-payment',
    'modal-edit-court', 'modal-booking-detail', 'modal-user-profile',
    'booking-lock-radar-modal', 'ai-slot-alert-modal', 'modal-confirm-logout',
    'modal-doi-mat-khau'
]

print("=== MODAL LIGHT MODE AUDIT ===")
for m in modals:
    # check occurrences with light theme
    light_matches = re.findall(rf'html\[data-theme=["\']light["\']\].*?#{m}', content)
    # also check if general .modal-card has light theme styles
    print(f"{m}: {len(light_matches)} light-mode specific rules found")

modal_card_light = re.findall(r'html\[data-theme=["\']light["\']\].*?\.modal-card', content)
print(f"General .modal-card in light mode: {len(modal_card_light)} rules found")
