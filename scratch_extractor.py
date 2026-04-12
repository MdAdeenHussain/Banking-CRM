import os
import re

TEMPLATE_DIR = 'app/templates'
CSS_DIR = 'app/static/css'
JS_DIR = 'app/static/js'

# Regex patterns
style_pattern = re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)
script_pattern = re.compile(r'<script(?! src)[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    rel_path = os.path.relpath(filepath, TEMPLATE_DIR)
    dir_name = os.path.dirname(rel_path)
    base_name = os.path.splitext(os.path.basename(rel_path))[0]
    
    styles = style_pattern.findall(content)
    scripts = script_pattern.findall(content)
    
    if not styles and not scripts:
        return
        
    has_jinja_in_script = any('{{' in s or '{%' in s for s in scripts)
    has_jinja_in_style = any('{{' in s or '{%' in s for s in styles)

    print(f"Processing: {rel_path}")
    
    if has_jinja_in_script:
        print(f"  WARNING: Skipping script extraction for {rel_path} because it contains Jinja tags.")
        scripts = [] # Do not extract scripts if they have Jinja tags
        content = script_pattern.sub(lambda m: '<script>' + m.group(1) + '</script>' if ('{{' in m.group(1) or '{%' in m.group(1)) else m.group(0), content)
        
    # We will only pull out scripts/styles that DO NOT contain Jinja tags.
    # To do this safely, let's substitute only matching groups that have no Jinja.
    
    valid_styles = []
    def style_replacer(match):
        css_content = match.group(1)
        if '{{' in css_content or '{%' in css_content:
            return match.group(0) # Do not touch
        valid_styles.append(css_content.strip())
        return ''
        
    content = style_pattern.sub(style_replacer, content)
    
    valid_scripts = []
    def script_replacer(match):
        js_content = match.group(1)
        if '{{' in js_content or '{%' in js_content:
            return match.group(0) # Do not touch
        valid_scripts.append(js_content.strip())
        return ''
        
    content = script_pattern.sub(script_replacer, content)

    if not valid_styles and not valid_scripts:
        print(f"  Nothing to extract (everything was Jinja text)")
        return
        
    css_links = ""
    if valid_styles:
        # Save to css file
        out_dir = os.path.join(CSS_DIR, dir_name)
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, f"{base_name}.css")
        
        with open(out_file, 'a', encoding='utf-8') as f:
            for s in valid_styles:
                f.write(s + "\n\n")
        
        href_path = f"css/{dir_name}/{base_name}.css".replace('\\', '/')
        if href_path.startswith('css//'):
            href_path = href_path.replace('css//', 'css/')
        css_links = f"<link rel=\"stylesheet\" href=\"{{{{ url_for('static', filename='{href_path}') }}}}\">"
        print(f"  -> Extracted {len(valid_styles)} style blocks to {out_file}")

    js_links = ""
    if valid_scripts:
        out_dir = os.path.join(JS_DIR, dir_name)
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, f"{base_name}.js")
        
        with open(out_file, 'a', encoding='utf-8') as f:
            for s in valid_scripts:
                f.write(s + "\n\n")
                
        src_path = f"js/{dir_name}/{base_name}.js".replace('\\', '/')
        if src_path.startswith('js//'):
            src_path = src_path.replace('js//', 'js/')
        js_links = f"<script src=\"{{{{ url_for('static', filename='{src_path}') }}}}\"></script>"
        print(f"  -> Extracted {len(valid_scripts)} script blocks to {out_file}")

    # Inject block extra_css if we have css
    if css_links:
        if '{% block extra_css %}' in content:
            content = content.replace('{% block extra_css %}', f'{{% block extra_css %}}\n{css_links}')
        else:
            content += f"\n{{% block extra_css %}}\n{css_links}\n{{% endblock %}}\n"
            
    # Inject block extra_js if we have js
    if js_links:
        if '{% block extra_js %}' in content:
            content = content.replace('{% block extra_js %}', f'{{% block extra_js %}}\n{js_links}')
        else:
            content += f"\n{{% block extra_js %}}\n{js_links}\n{{% endblock %}}\n"

    # Write modified html back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk(TEMPLATE_DIR):
    for filename in files:
        if filename.endswith('.html'):
            filepath = os.path.join(root, filename)
            process_file(filepath)

print("Extraction script completed.")
