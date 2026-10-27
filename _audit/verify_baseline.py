import re
import json
import os
import sys
from html.parser import HTMLParser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
AUDIT_DIR = os.path.join(BASE_DIR, "_audit")
app_path = os.path.join(FRONTEND_DIR, "app.html")
INDEX_HTML_PATH = app_path if os.path.exists(app_path) else os.path.join(FRONTEND_DIR, "index.html")
BASELINE_PATH = os.path.join(AUDIT_DIR, "baseline.json")

class CurrentHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.names = set()
        self.data_tabs = set()
        self.data_views = set()
        self.data_sports = set()
        self.data_statuses = set()
        self.data_prompts = set()
        self.onclicks = []
        self.display_none_ids = set()
        self.display_none_count = 0

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        el_id = attr_dict.get('id')
        
        if 'id' in attr_dict:
            self.ids.add(attr_dict['id'])
        if 'name' in attr_dict:
            self.names.add(attr_dict['name'])
        if 'data-tab' in attr_dict:
            self.data_tabs.add(attr_dict['data-tab'])
        if 'data-view' in attr_dict:
            self.data_views.add(attr_dict['data-view'])
        if 'data-sport' in attr_dict:
            self.data_sports.add(attr_dict['data-sport'])
        if 'data-status' in attr_dict:
            self.data_statuses.add(attr_dict['data-status'])
        if 'data-prompt' in attr_dict:
            self.data_prompts.add(attr_dict['data-prompt'])
        if 'onclick' in attr_dict:
            self.onclicks.append({'id': el_id, 'onclick': attr_dict['onclick']})
            
        style = attr_dict.get('style', '')
        if 'display:none' in style.replace(' ', '') or 'display: none' in style:
            self.display_none_count += 1
            if el_id:
                self.display_none_ids.add(el_id)

def verify():
    if not os.path.exists(BASELINE_PATH):
        print("[FAIL] Baseline file does not exist!")
        sys.exit(1)
        
    with open(BASELINE_PATH, 'r', encoding='utf-8') as f:
        baseline = json.load(f)
        
    with open(INDEX_HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        
    parser = CurrentHTMLParser()
    parser.feed(content)
    
    errors = []
    
    # 1. Check IDs
    base_ids = set(baseline["ids"])
    missing_ids = base_ids - parser.ids
    if missing_ids:
        errors.append(f"Missing IDs ({len(missing_ids)}): {list(missing_ids)[:10]}")
        
    # 2. Check Names
    base_names = set(baseline["names"])
    missing_names = base_names - parser.names
    if missing_names:
        errors.append(f"Missing Names: {missing_names}")
        
    # 3. Check data attributes
    if set(baseline["data_tabs"]) - parser.data_tabs:
        errors.append(f"Missing data-tab: {set(baseline['data_tabs']) - parser.data_tabs}")
    if set(baseline["data_views"]) - parser.data_views:
        errors.append(f"Missing data-view: {set(baseline['data_views']) - parser.data_views}")
    if set(baseline["data_sports"]) - parser.data_sports:
        errors.append(f"Missing data-sport: {set(baseline['data_sports']) - parser.data_sports}")
    if set(baseline["data_statuses"]) - parser.data_statuses:
        errors.append(f"Missing data-status: {set(baseline['data_statuses']) - parser.data_statuses}")
    if set(baseline["data_prompts"]) - parser.data_prompts:
        errors.append(f"Missing data-prompt: {set(baseline['data_prompts']) - parser.data_prompts}")
        
    # 4. Check display:none elements
    base_display_none_ids = {item["id"] for item in baseline["display_none_elements"] if item.get("id")}
    missing_display_none = base_display_none_ids - parser.display_none_ids
    if missing_display_none:
        errors.append(f"Elements lost required style='display:none': {missing_display_none}")
        
    # 5. Check onclick count
    if len(parser.onclicks) < baseline["onclick_count"]:
        errors.append(f"Onclick count dropped from {baseline['onclick_count']} to {len(parser.onclicks)}")
        
    print("=" * 60)
    print("BASELINE DOM VERIFICATION REPORT")
    print("=" * 60)
    print(f"Total IDs: {len(parser.ids)} / baseline {len(base_ids)}")
    print(f"Total Names: {len(parser.names)} / baseline {len(base_names)}")
    print(f"Total display:none elements: {parser.display_none_count} / baseline {len(baseline['display_none_elements'])}")
    print(f"Total onclick handlers: {len(parser.onclicks)} / baseline {baseline['onclick_count']}")
    
    if errors:
        print("\n[RESULT: FAIL]")
        for err in errors:
            print(f" - {err}")
        return False
    else:
        print("\n[RESULT: PASS] 100% DOM attributes preserved perfectly.")
        return True

if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
