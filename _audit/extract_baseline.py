import re
import json
import os
from html.parser import HTMLParser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
AUDIT_DIR = os.path.join(BASE_DIR, "_audit")
os.makedirs(AUDIT_DIR, exist_ok=True)

INDEX_HTML_PATH = os.path.join(FRONTEND_DIR, "index.html")
APP_JS_PATH = os.path.join(FRONTEND_DIR, "js", "app.js")
STYLE_CSS_PATH = os.path.join(FRONTEND_DIR, "css", "style.css")

class IndexHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.names = []
        self.data_tabs = []
        self.data_views = []
        self.data_sports = []
        self.data_statuses = []
        self.data_prompts = []
        self.onlicks = []
        self.display_none_elements = [] # (tag, id, class, inline_style)
        self.all_elements_with_style = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        el_id = attr_dict.get('id')
        el_class = attr_dict.get('class', '')
        
        if 'id' in attr_dict:
            self.ids.append(attr_dict['id'])
        if 'name' in attr_dict:
            self.names.append(attr_dict['name'])
        if 'data-tab' in attr_dict:
            self.data_tabs.append(attr_dict['data-tab'])
        if 'data-view' in attr_dict:
            self.data_views.append(attr_dict['data-view'])
        if 'data-sport' in attr_dict:
            self.data_sports.append(attr_dict['data-sport'])
        if 'data-status' in attr_dict:
            self.data_statuses.append(attr_dict['data-status'])
        if 'data-prompt' in attr_dict:
            self.data_prompts.append(attr_dict['data-prompt'])
        if 'onclick' in attr_dict:
            self.onlicks.append({'id': el_id, 'tag': tag, 'onclick': attr_dict['onclick']})
            
        style = attr_dict.get('style', '')
        if style:
            self.all_elements_with_style.append({'tag': tag, 'id': el_id, 'class': el_class, 'style': style})
            if 'display:none' in style.replace(' ', '') or 'display: none' in style:
                self.display_none_elements.append({'tag': tag, 'id': el_id, 'class': el_class, 'style': style})

def extract_html_baseline():
    with open(INDEX_HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = IndexHTMLParser()
    parser.feed(content)
    
    baseline = {
        "ids": sorted(list(set(parser.ids))),
        "names": sorted(list(set(parser.names))),
        "data_tabs": sorted(list(set(parser.data_tabs))),
        "data_views": sorted(list(set(parser.data_views))),
        "data_sports": sorted(list(set(parser.data_sports))),
        "data_statuses": sorted(list(set(parser.data_statuses))),
        "data_prompts": sorted(list(set(parser.data_prompts))),
        "onclick_count": len(parser.onlicks),
        "onclicks": parser.onlicks,
        "display_none_elements": parser.display_none_elements,
        "all_elements_with_style": parser.all_elements_with_style
    }
    
    baseline_path = os.path.join(AUDIT_DIR, "baseline.json")
    with open(baseline_path, 'w', encoding='utf-8') as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)
    print(f"[OK] Extracted HTML baseline: {len(baseline['ids'])} IDs, {len(baseline['names'])} Names, {len(baseline['display_none_elements'])} display:none elements.")
    return baseline

def extract_js_selectors():
    with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
        js_content = f.read()

    # 1. getElementById
    get_el_ids = set(re.findall(r"getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)", js_content))
    
    # 2. querySelector / querySelectorAll
    qs_matches = set(re.findall(r"querySelector(?:All)?\(\s*['\"]([^'\"]+)['\"]\s*\)", js_content))
    
    # 3. classList add/remove/toggle/contains
    class_list_ops = set(re.findall(r"classList\.(?:add|remove|toggle|contains)\(\s*['\"]([^'\"]+)['\"]\s*\)", js_content))
    
    # 4. className assignments
    class_name_assigns = set(re.findall(r"\.className\s*=\s*['\"]([^'\"]+)['\"]", js_content))
    
    # 5. Template strings class="..."
    template_classes = set()
    for m in re.findall(r"class=['\"]([^'\"]+)['\"]", js_content):
        for c in m.split():
            c = c.strip()
            # filter out template interpolations like ${...}
            if c and not c.startswith('$') and not '{' in c and not '}' in c:
                template_classes.add(c)
                
    # 6. Animation timings: setTimeout with class manipulations or animationend/transitionend
    lines = js_content.split('\n')
    timing_contexts = []
    for i, line in enumerate(lines):
        if 'setTimeout' in line:
            # find timeout duration in this or subsequent 3 lines
            chunk = "\n".join(lines[max(0, i-2):min(len(lines), i+4)])
            m = re.search(r",\s*(\d{2,5})\s*\)", chunk)
            duration = int(m.group(1)) if m else None
            # look for class references
            classes_in_chunk = re.findall(r"classList\.(?:add|remove|toggle)\(\s*['\"]([^'\"]+)['\"]\s*\)", chunk)
            classes_in_chunk += re.findall(r"['\"]([a-zA-Z0-9\-_]*(?:anim|fade|slide|shake|modal|overlay|toast|active|show|enter|leave)[a-zA-Z0-9\-_]*)['\"]", chunk)
            if duration or classes_in_chunk:
                timing_contexts.append({
                    "line": i + 1,
                    "code_snippet": line.strip(),
                    "duration_ms": duration,
                    "related_classes": list(set(classes_in_chunk))
                })
        if 'addEventListener' in line and ('animationend' in line or 'transitionend' in line):
            chunk = "\n".join(lines[max(0, i-2):min(len(lines), i+6)])
            timing_contexts.append({
                "line": i + 1,
                "event": "animationend/transitionend",
                "code_snippet": line.strip(),
                "context": chunk
            })

    must_keep = {
        "get_element_by_id": sorted(list(get_el_ids)),
        "query_selectors": sorted(list(qs_matches)),
        "class_list_methods": sorted(list(class_list_ops)),
        "class_name_assignments": sorted(list(class_name_assigns)),
        "template_dynamic_classes": sorted(list(template_classes)),
        "all_classes_union": sorted(list(class_list_ops.union(class_name_assigns).union(template_classes)))
    }
    
    must_keep_path = os.path.join(AUDIT_DIR, "must_keep_selectors.json")
    with open(must_keep_path, 'w', encoding='utf-8') as f:
        json.dump(must_keep, f, ensure_ascii=False, indent=2)

    timings_path = os.path.join(AUDIT_DIR, "animation_timings.json")
    with open(timings_path, 'w', encoding='utf-8') as f:
        json.dump(timing_contexts, f, ensure_ascii=False, indent=2)

    print(f"[OK] Extracted JS selectors: {len(get_el_ids)} getElementById, {len(qs_matches)} querySelectors, {len(must_keep['all_classes_union'])} classes.")
    print(f"[OK] Extracted JS timing contexts: {len(timing_contexts)} instances.")

if __name__ == "__main__":
    extract_html_baseline()
    extract_js_selectors()
