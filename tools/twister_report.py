#!/usr/bin/env python3
"""
Twister Report Analyzer — Meaningful Edition
ניתוח משמעותי של תוצאות הבנייה — לא תיאורים כלליים
"""

import json
import os
import sys
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from html import escape

def load_json_file(path: Path) -> dict:
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def load_text_file(path: Path) -> str:
    if not path.exists(): return ""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f: return f.read()

def parse_xml_file(path: Path) -> dict:
    if not path.exists(): return {}
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        data = {"testsuites": []}
        for testsuite in root.findall('.//testsuite'):
            suite = {
                "name": testsuite.get("name", ""),
                "tests": int(testsuite.get("tests", 0)),
                "failures": int(testsuite.get("failures", 0)),
                "errors": int(testsuite.get("errors", 0)),
                "skipped": int(testsuite.get("skipped", 0)),
                "properties": {},
                "testcases": []
            }
            for prop in testsuite.findall('.//property'):
                suite["properties"][prop.get("name", "")] = prop.get("value", "")
            for tc in testsuite.findall('.//testcase'):
                testcase = {"name": tc.get("name", ""), "status": "passed", "message": ""}
                skipped = tc.find('skipped')
                if skipped is not None:
                    testcase["status"] = "skipped"
                    testcase["message"] = skipped.get("message", "")
                failure = tc.find('failure')
                if failure is not None:
                    testcase["status"] = "failed"
                    testcase["message"] = failure.get("message", "")
                suite["testcases"].append(testcase)
            data["testsuites"].append(suite)
        return data
    except: return {}

def generate_meaningful_interpretation(twister_out_path: Path) -> str:
    """Generate a meaningful interpretation of what happened"""
    
    # Load all data
    twister_json = load_json_file(twister_out_path / "twister.json")
    testplan_json = load_json_file(twister_out_path / "testplan.json")
    twister_log = load_text_file(twister_out_path / "twister.log")
    report_xml = parse_xml_file(twister_out_path / "twister_report.xml")
    
    env = twister_json.get("environment", {})
    options = env.get("options", {})
    testsuites = twister_json.get("testsuites", [])
    
    # Extract key facts
    passed = sum(1 for t in testsuites if t.get("status") == "passed")
    failed = sum(1 for t in testsuites if t.get("status") == "failed")
    errored = sum(1 for t in testsuites if t.get("status") == "error")
    skipped = sum(1 for t in testsuites if t.get("status") == "skipped")
    total = len(testsuites)
    
    build_only = options.get("build_only", False)
    force_platform = options.get("force_platform", False)
    platforms = options.get("platform", [])
    testsuite_roots = options.get("testsuite_root", [])
    
    platform_name = platforms[0] if platforms else "לא ידוע"
    app_name = testsuite_roots[0].split("/")[-1] if testsuite_roots else "לא ידוע"
    
    build_time = sum(float(t.get("build_time", 0)) for t in testsuites)
    
    # Get skip reasons from XML
    skip_reasons = []
    for suite in report_xml.get("testsuites", []):
        for tc in suite.get("testcases", []):
            if tc.get("status") == "skipped" and tc.get("message"):
                skip_reasons.append(tc["message"])
    
    # BUILD MEANINGFUL INTERPRETATION
    interpretation_sections = []
    
    # 1. מה עשית?
    if build_only:
        action = f"ביצעת בנייה (קומפילציה) של האפליקציה <strong>{app_name}</strong> עבור הלוח <strong>{platform_name}</strong>."
        if force_platform:
            action += "<br><br>השתמשת ב-<code>--force-platform</code> כדי לאלץ בנייה גם שהלוח הזה לא מופיע ברשימת הלוחות המאושרים לאפליקציה הזו."
    else:
        action = f"ביקשת לבנות ולהריץ טסטים על האפליקציה <strong>{app_name}</strong> עבור הלוח <strong>{platform_name}</strong>."
    
    interpretation_sections.append({
        "title": "מה עשית?",
        "icon": "🎯",
        "content": action
    })
    
    # 2. מה קרה?
    if passed == total and total > 0:
        outcome = f"""
        <div class="outcome success">
            הבנייה <strong>הצליחה לחלוטין</strong>.
            <br><br>
            נוצר קובץ firmware מוכן להעברה ללוח. הקובץ נמצא בתיקייה:
            <br><code>twister-out/{platform_name.replace('/', '_')}/...</code>
            <br><br>
            <strong>הצעד הבא:</strong> ניתן להעביר את הקובץ ללוח באמצעות <code>west flash</code>.
        </div>
        """
    elif failed + errored > 0:
        outcome = f"""
        <div class="outcome danger">
            הבנייה <strong>נכשלה</strong>.
            <br><br>
            {failed + errored} קונפיגורציות לא הצליחו להתקמפל. יש לבדוק את שגיאות הקומפילציה בקובץ <code>build.log</code> בתוך תיקיית הפלט.
            <br><br>
            <strong>הצעד הבא:</strong> תקן את שגיאות הקומפילציה והרץ שוב.
        </div>
        """
    elif skipped == total:
        outcome = f"""
        <div class="outcome warning">
            <strong>לא בוצעה בנייה בפועל</strong> — כל הקונפיגורציות דולגו.
            <br><br>
            הסיבה: הלוח שנבחר (<code>{platform_name}</code>) לא מופיע ברשימת <code>platform_allow</code> בקובץ <code>testcase.yaml</code> של האפליקציה.
            <br><br>
            <strong>הצעד הבא:</strong> הוסף <code>--force-platform</code> לפקודה כדי לאלץ בנייה.
        </div>
        """
    else:
        outcome = "<div class='outcome'>לא נמצאו תוצאות</div>"
    
    interpretation_sections.append({
        "title": "מה קרה?",
        "icon": "📊",
        "content": outcome
    })
    
    # 3. למה הטסטים לא רצו?
    if build_only and skip_reasons:
        reason = skip_reasons[0] if skip_reasons else ""
        if "built only" in reason.lower():
            tests_explanation = """
            <strong>הטסטים לא רצו כי השתמשת ב-<code>--build-only</code></strong>.
            <br><br>
            דגל זה אומר ל-Twister: "רק תבנה את הקוד, אל תנסה להריץ אותו על הלוח או בסימולציה".
            <br><br>
            זה שימושי כשאתה רוצה לוודא שהקוד מתקמפל בלי טעויות, לפני שאתה מחבר את הלוח או מעביר אליו את הקוד.
            """
            interpretation_sections.append({
                "title": "למה הטסטים לא רצו?",
                "icon": "⏭️",
                "content": tests_explanation
            })
    
    # 4. כמה זמן לקח?
    if build_time > 0:
        time_explanation = f"""
        הבנייה לקחה <strong>{build_time:.1f} שניות</strong>.
        <br><br>
        זמן זה כולל:
        <ul>
            <li>יצירת קבצי CMake</li>
            <li>קומפילציה של קוד ה-C</li>
            <li>לינקור (linking) של כל הספריות</li>
            <li>יצירת קובץ הבינארי הסופי</li>
        </ul>
        """
        interpretation_sections.append({
            "title": "כמה זמן לקח?",
            "icon": "⏱️",
            "content": time_explanation
        })
    
    # 5. מה עכשיו?
    next_steps = []
    if passed == total and total > 0:
        next_steps.append("הקובץ הבינארי מוכן — ניתן להעביר אותו ללוח עם <code>west flash</code>")
        next_steps.append("אם רוצים לוודא שהטסטים עוברים, הסר את <code>--build-only</code>")
    elif failed + errored > 0:
        next_steps.append("פתח את <code>build.log</code> ובדוק את השגיאות")
        next_steps.append("תקן את הקוד או ההגדרות והרץ שוב")
    elif skipped == total:
        next_steps.append("הוסף <code>--force-platform</code> לפקודה")
        next_steps.append("או הוסף את הלוח ל-<code>platform_allow</code> בקובץ <code>testcase.yaml</code>")
    
    if next_steps:
        next_html = "<ul>" + "".join(f"<li>{s}</li>" for s in next_steps) + "</ul>"
        interpretation_sections.append({
            "title": "מה הצעד הבא?",
            "icon": "🚀",
            "content": next_html
        })
    
    # Build sections HTML
    sections_html = ""
    for section in interpretation_sections:
        sections_html += f'''
        <div class="section">
            <h2 class="section-title"><span class="section-icon">{section["icon"]}</span>{section["title"]}</h2>
            <div class="section-content">{section["content"]}</div>
        </div>
        '''
    
    # Summary banner
    if passed == total and total > 0:
        banner_class, banner_icon, banner_text = "success", "✅", "הבנייה הושלמה בהצלחה"
    elif failed + errored > 0:
        banner_class, banner_icon, banner_text = "danger", "❌", "הבנייה נכשלה"
    elif skipped == total:
        banner_class, banner_icon, banner_text = "warning", "⏭️", "הבנייה דולגה"
    else:
        banner_class, banner_icon, banner_text = "info", "❓", "אין תוצאות"
    
    html = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ניתוח משמעותי — {app_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0a0a0f;
            --card: rgba(255,255,255,0.03);
            --border: rgba(255,255,255,0.08);
            --text: #fff;
            --text2: rgba(255,255,255,0.7);
            --text3: rgba(255,255,255,0.4);
            --green: #10b981;
            --red: #ef4444;
            --yellow: #f59e0b;
            --blue: #3b82f6;
            --purple: #8b5cf6;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Heebo', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.8;
            padding: 2rem;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        
        .header {{ text-align: center; margin-bottom: 2rem; }}
        .header h1 {{
            font-size: 2rem;
            background: linear-gradient(135deg, var(--blue), var(--purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        .header .meta {{ color: var(--text3); font-size: 0.9rem; }}
        
        .banner {{
            padding: 1.5rem 2rem;
            border-radius: 1rem;
            text-align: center;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 2rem;
        }}
        .banner.success {{ background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(16,185,129,0.05)); border: 1px solid rgba(16,185,129,0.3); }}
        .banner.danger {{ background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.05)); border: 1px solid rgba(239,68,68,0.3); }}
        .banner.warning {{ background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.05)); border: 1px solid rgba(245,158,11,0.3); }}
        .banner.info {{ background: var(--card); border: 1px solid var(--border); }}
        .banner-icon {{ font-size: 2rem; display: block; margin-bottom: 0.5rem; }}
        
        .section {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
        }}
        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        .section-icon {{ font-size: 1.5rem; }}
        .section-content {{
            color: var(--text2);
            font-size: 1.05rem;
        }}
        .section-content strong {{ color: var(--text); }}
        .section-content code {{
            background: rgba(139,92,246,0.2);
            color: var(--purple);
            padding: 0.15rem 0.4rem;
            border-radius: 0.25rem;
            font-size: 0.9rem;
        }}
        .section-content ul {{
            margin-top: 0.75rem;
            margin-right: 1.5rem;
        }}
        .section-content li {{ margin-bottom: 0.5rem; }}
        
        .outcome {{
            padding: 1.25rem;
            border-radius: 0.75rem;
            margin-top: 0.5rem;
        }}
        .outcome.success {{ background: rgba(16,185,129,0.1); border-right: 4px solid var(--green); }}
        .outcome.danger {{ background: rgba(239,68,68,0.1); border-right: 4px solid var(--red); }}
        .outcome.warning {{ background: rgba(245,158,11,0.1); border-right: 4px solid var(--yellow); }}
        
        .footer {{
            text-align: center;
            color: var(--text3);
            font-size: 0.85rem;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(15px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .section {{ animation: fadeIn 0.4s ease forwards; opacity: 0; }}
        .section:nth-child(2) {{ animation-delay: 0.1s; }}
        .section:nth-child(3) {{ animation-delay: 0.2s; }}
        .section:nth-child(4) {{ animation-delay: 0.3s; }}
        .section:nth-child(5) {{ animation-delay: 0.4s; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 ניתוח משמעותי של הבנייה</h1>
            <p class="meta">{app_name} על {platform_name} | {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        </div>
        
        <div class="banner {banner_class}">
            <span class="banner-icon">{banner_icon}</span>
            {banner_text}
        </div>
        
        {sections_html}
        
        <div class="footer">
            דוח זה מספק פרשנות משמעותית של תוצאות הבנייה — לא רק נתונים גולמיים
        </div>
    </div>
</body>
</html>
'''
    
    html_path = twister_out_path / "report.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return str(html_path)

def main():
    if len(sys.argv) > 1:
        twister_out = Path(sys.argv[1])
    else:
        twister_out = Path("twister-out")
        if not twister_out.exists():
            twister_out = Path("zephyr/twister-out")
    
    if not twister_out.exists():
        print(f"❌ לא נמצאה תיקייה: {twister_out}")
        sys.exit(1)
    
    print(f"📂 מנתח: {twister_out}")
    try:
        html_path = generate_meaningful_interpretation(twister_out)
        print(f"✅ נוצר דוח: {html_path}")
        webbrowser.open(f"file://{os.path.abspath(html_path)}")
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
