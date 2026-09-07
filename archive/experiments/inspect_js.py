import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if script_match:
    js_code = script_match.group(1)
    
# Let's inspect the lines in static/index.html around 1400-1480
lines = html.split('\n')
for i, line in enumerate(lines[1410:1470], start=1411):
    print(f"{i:4d}: {line}")
