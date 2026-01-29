from flask import Flask, request, send_file, render_template, jsonify
import subprocess, tempfile, os, textwrap, json

app = Flask(__name__)

# -----------------------------
# Helpers
# -----------------------------
def esc(s: str) -> str:
    """Escape LaTeX special characters in user content (not URLs)."""
    if s is None: return ""
    repl = {
        '\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
        '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'
    }
    out = []
    for ch in s:
        out.append(repl.get(ch, ch))
    return "".join(out)


def _has_non_latin(s: str) -> bool:
    """True if string contains Arabic or other non-Latin script (pdflatex cannot handle)."""
    if not s or not isinstance(s, str):
        return False
    for ch in s:
        code = ord(ch)
        if (0x0600 <= code <= 0x06FF) or (0x0750 <= code <= 0x077F) or (0x08A0 <= code <= 0x08FF):
            return True
    return False


def payload_has_non_latin(obj) -> bool:
    """Recursively check if payload contains any string with non-Latin (e.g. Arabic) characters."""
    if isinstance(obj, str):
        return _has_non_latin(obj)
    if isinstance(obj, dict):
        return any(payload_has_non_latin(v) for v in obj.values())
    if isinstance(obj, list):
        return any(payload_has_non_latin(v) for v in obj)
    return False

def bullets_to_items(bullets):
    if not bullets: return ""
    lines = []
    for b in bullets:
        if not b: continue
        lines.append(rf"      \resumeItem{{{esc(b)}}}")
    return "\n".join(lines)

def make_subheading(title, dates, org, location):
    # Title may be raw LaTeX (e.g. \href{url}{text}) from projects/publications; do not escape it
    raw = title.strip()
    is_raw_latex = raw.startswith("\\") or "\\href" in title
    title_tex = title if is_raw_latex else esc(title)
    return textwrap.dedent(rf"""
    \resumeSubheading
      {{{title_tex}}}{{{esc(dates)}}}
      {{{esc(org)}}}{{{esc(location)}}}
    """).strip()

def build_education(data):
    # data: list of {university, location, degree, date}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for e in data:
        out.append(make_subheading(e.get("university",""), e.get("date",""), e.get("degree",""), e.get("location","")))
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_experience(data):
    # data: list of {title, company, location, dates, bullets: []}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for x in data:
        out.append(make_subheading(x.get("title",""), x.get("dates",""), x.get("company",""), x.get("location","")))
        if x.get("bullets"):
            out.append(r"    \vspace{4px}")
            out.append(r"    \resumeItemListStart")
            out.append(bullets_to_items(x["bullets"]))
            out.append(r"    \resumeItemListEnd")
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_projects(data):
    # data: list of {name, dates, description, link, bullets: []}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for p in data:
        name = p.get("name","")
        link = p.get("link","")
        if link and link.strip():
            # Make project name a clickable link (display text escaped for LaTeX)
            name = rf"\href{{{link}}}{{{esc(name)}}}"
        out.append(make_subheading(name, p.get("dates",""), p.get("description",""), ""))  # 4th column empty
        if p.get("bullets"):
            out.append(r"    \vspace{2px}")
            out.append(r"    \resumeItemListStart")
            out.append(bullets_to_items(p["bullets"]))
            out.append(r"    \resumeItemListEnd")
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_publications(data):
    # data: list of {title, date, publisher, link, bullets: []}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for p in data:
        title = p.get("title","")
        link = p.get("link","")
        if link and link.strip():
            # Make publication title a clickable link (display text escaped for LaTeX)
            title = rf"\href{{{link}}}{{{esc(title)}}}"
        out.append(make_subheading(title, p.get("date",""), p.get("publisher",""), ""))
        if p.get("bullets"):
            out.append(r"    \vspace{2px}")
            out.append(r"    \resumeItemListStart")
            out.append(bullets_to_items(p["bullets"]))
            out.append(r"    \resumeItemListEnd")
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_skills(skills):
    # skills: dict like {"Programming Languages": ["Python","Java"], "Frameworks":["React","Spring"]}
    if not skills: return ""
    out = [r"\resumeSubHeadingList"]
    for k, arr in skills.items():
        line = f"\\resumeItem{{\\textbf{{{esc(k)}}}: {esc(', '.join(arr))}}}"
        out.append(line)
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_certifications(data):
    # data: list of {name, date, provider}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for c in data:
        out.append(make_subheading(c.get("name",""), c.get("date",""), c.get("provider",""), ""))
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_research_experience(data):
    # data: list of {title, company, location, dates, bullets: []}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for x in data:
        out.append(make_subheading(x.get("title",""), x.get("dates",""), x.get("company",""), x.get("location","")))
        if x.get("bullets"):
            out.append(r"    \vspace{4px}")
            out.append(r"    \resumeItemListStart")
            out.append(bullets_to_items(x["bullets"]))
            out.append(r"    \resumeItemListEnd")
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_industry_experience(data):
    # data: list of {title, company, location, dates, bullets: []}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for x in data:
        out.append(make_subheading(x.get("title",""), x.get("dates",""), x.get("company",""), x.get("location","")))
        if x.get("bullets"):
            out.append(r"    \vspace{4px}")
            out.append(r"    \resumeItemListStart")
            out.append(bullets_to_items(x["bullets"]))
            out.append(r"    \resumeItemListEnd")
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_honors_awards(data):
    # data: list of {title, company, location, dates, bullets: []}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for x in data:
        out.append(make_subheading(x.get("title",""), x.get("dates",""), x.get("company",""), x.get("location","")))
        if x.get("bullets"):
            out.append(r"    \resumeItemListStart")
            out.append(bullets_to_items(x["bullets"]))
            out.append(r"    \resumeItemListEnd")
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_volunteering(data):
    # data: list of {title, company, location, dates, bullets: []}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for x in data:
        out.append(make_subheading(x.get("title",""), x.get("dates",""), x.get("company",""), x.get("location","")))
        if x.get("bullets"):
            out.append(r"    \vspace{4px}")
            out.append(r"    \resumeItemListStart")
            out.append(bullets_to_items(x["bullets"]))
            out.append(r"    \resumeItemListEnd")
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_custom_sections(custom_sections):
    # custom_sections: [{title, blocks:[{title, dates, org, location, bullets:[]}] }]
    if not custom_sections: return ""
    out = []
    for sec in custom_sections:
        title = sec.get("title","Custom")
        out.append(f"\\vspace{{-2ex}}\n\\section{{{esc(title)}}}")
        out.append(r"\resumeSubHeadingList")
        for b in sec.get("blocks", []):
            out.append(make_subheading(b.get("title",""), b.get("dates",""), b.get("org",""), b.get("location","")))
            if b.get("bullets"):
                out.append(r"    \vspace{4px}")
                out.append(r"    \resumeItemListStart")
                out.append(bullets_to_items(b["bullets"]))
                out.append(r"    \resumeItemListEnd")
        out.append(r"\resumeSubHeadingListEnd")
        out.append("")  # spacer
    return "\n".join(out)

def _safe_url(url: str) -> str:
    """Return URL for LaTeX \\href; use # when empty to avoid invalid \\href{}{}."""
    s = (url or "").strip()
    return s if s else "#"


def build_header(u):
    # Build header LaTeX code directly for better control over empty values
    name = esc(u.get("name", ""))
    if not name:
        return {"HEADER": ""}
    
    # Name
    header_tex = f"  \\textbf{{\\Huge {name}}}"
    
    # Contact info
    contact_parts = []
    phone = u.get("phone", "").strip()
    if phone:
        contact_parts.append(esc(phone))
    
    email = u.get("email", "").strip()
    if email:
        # Don't escape the email in the href URL, but escape the display text
        contact_parts.append(f"\\href{{mailto:{email}}}{{{esc(email)}}}")
    
    linkedin = u.get("linkedin", "").strip()
    if linkedin:
        linkedin_url = _safe_url(linkedin)
        if linkedin_url != "#":
            # Extract domain/path for display (simplified - show full URL for now)
            display = linkedin_url.replace("https://", "").replace("http://", "").rstrip("/")
            contact_parts.append(f"\\href{{{linkedin_url}}}{{{esc(display)}}}")
    
    github = u.get("github", "").strip()
    if github:
        github_url = _safe_url(github)
        if github_url != "#":
            display = github_url.replace("https://", "").replace("http://", "").rstrip("/")
            contact_parts.append(f"\\href{{{github_url}}}{{{esc(display)}}}")
    
    website = u.get("website", "").strip()
    if website:
        website_url = _safe_url(website)
        if website_url != "#":
            display = website_url.replace("https://", "").replace("http://", "").rstrip("/")
            contact_parts.append(f"\\href{{{website_url}}}{{{esc(display)}}}")
    
    # Custom headers
    custom_headers = u.get("custom_headers", [])
    for header in custom_headers[:3]:
        value = header.get("value", "").strip()
        if value:
            value_url = _safe_url(value)
            if value_url != "#":
                display = value_url.replace("https://", "").replace("http://", "").rstrip("/")
                contact_parts.append(f"\\href{{{value_url}}}{{{esc(display)}}}")
    
    # Join contact parts with separators (footnotesize so long line fits better)
    if contact_parts:
        contact_line = " $|$ ".join(contact_parts)
        header_tex += f" \\\\\n  \\vspace{{0.3cm}}\n  \\footnotesize\n  {contact_line}"
    
    return {"HEADER": header_tex}

# Map section names (as shown in UI) to builders (skip empty sections)
SECTION_BUILDERS = {
    "Summary": lambda d: "" if not (d.get("summary") or "").strip() else f"\\vspace{{0.5ex}}\n\\section*{{Summary}}\n{esc(d.get('summary',''))}\n",
    "Education": lambda d: "" if not d.get("education") else f"\\vspace{{-10px}}\n\\section{{Education}}\n{build_education(d.get('education'))}\n",
    "Experience": lambda d: "" if not d.get("experience") else f"\\vspace{{-2ex}}\n\\section{{Experience}}\n{build_experience(d.get('experience'))}\n",
    "Research Experience": lambda d: "" if not d.get("researchexperience") else f"\\section{{Research Experience}}\n{build_research_experience(d.get('researchexperience'))}\n",
    "Industry Experience": lambda d: "" if not d.get("industryexperience") else f"\\vspace{{-2ex}}\n\\section{{Industry Experience}}\n{build_industry_experience(d.get('industryexperience'))}\n",
    "Projects": lambda d: "" if not d.get("projects") else f"\\vspace{{-2ex}}\n\\section{{Projects}}\n{build_projects(d.get('projects'))}\n",
    "Skills": lambda d: "" if not d.get("skills") else f"\\vspace{{-2ex}}\n\\section{{Skills}}\n{build_skills(d.get('skills'))}\n",
    "Certifications": lambda d: "" if not d.get("certifications") else f"\\vspace{{-2ex}}\n\\section{{Certifications}}\n{build_certifications(d.get('certifications'))}\n",
    "Publications": lambda d: "" if not d.get("publications") else f"\\vspace{{-2ex}}\n\\section{{Publications}}\n{build_publications(d.get('publications'))}\n",
    "Honors & Awards": lambda d: "" if not d.get("honorsawards") else f"\\vspace{{-2ex}}\n\\section{{Honors \\& Awards}}\n{build_honors_awards(d.get('honorsawards'))}\n",
    "Volunteering": lambda d: "" if not d.get("volunteering") else f"\\vspace{{-2ex}}\n\\section{{Volunteering}}\n{build_volunteering(d.get('volunteering'))}\n",
}

DEFAULT_ORDER = [
    "Education", "Research Experience", "Industry Experience", "Publications", "Projects", "Skills", "Honors & Awards", "Volunteering", "Certifications"
]

def build_sections_latex(payload):
    order = payload.get("order") or DEFAULT_ORDER
    section_names = payload.get("section_names", {})
    parts = []
    seen = set()

    # Add selected built-in sections in chosen order
    for name in order:
        b = SECTION_BUILDERS.get(name)
        if b:
            # Use custom section name if available
            section_id = name.lower().replace(" ", "")
            custom_name = section_names.get(section_id, name)
            section_tex = b(payload)
            if not section_tex.strip():
                seen.add(name)
                continue
            if custom_name != name:
                # Replace the section name in the LaTeX
                section_tex = section_tex.replace(f"\\section{{{name}}}", f"\\section{{{custom_name}}}")
                section_tex = section_tex.replace(f"\\section*{{{name}}}", f"\\section*{{{custom_name}}}")
            parts.append(section_tex)
            seen.add(name)

    # Append any built-in sections not in order but present in data
    for name, builder in SECTION_BUILDERS.items():
        if name not in seen and payload.get(name.lower().replace(" ", "")):
            section_id = name.lower().replace(" ", "")
            custom_name = section_names.get(section_id, name)
            section_tex = builder(payload)
            if not section_tex.strip():
                continue
            if custom_name != name:
                section_tex = section_tex.replace(f"\\section{{{name}}}", f"\\section{{{custom_name}}}")
                section_tex = section_tex.replace(f"\\section*{{{name}}}", f"\\section*{{{custom_name}}}")
            parts.append(section_tex)

    # Custom sections (can be placed anywhere via "order" using "Custom:<Title>")
    # If user put "Custom:<Title>" inside order, we respect that position.
    # Otherwise we append all customs at the end.
    custom_by_title = { (cs.get("title") or "Custom"): cs for cs in (payload.get("custom_sections") or []) }

    # process ordered customs
    for name in order:
        if name.startswith("Custom:"):
            title = name.split("Custom:",1)[1].strip()
            cs = custom_by_title.pop(title, None)
            if cs:
                parts.append(build_custom_sections([cs]))

    # append remaining customs (unordered)
    if custom_by_title:
        parts.append(build_custom_sections(list(custom_by_title.values())))

    return "\n".join(parts)

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/example-cv", methods=["GET"])
def get_example_cv():
    try:
        import os
        json_path = os.path.join(os.path.dirname(__file__), "example_cv.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": f"Example CV not found at {json_path}"}), 404
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/generate-cv", methods=["POST"])
def generate_cv():
    payload = request.get_json(force=True)

    # English-only: pdflatex cannot handle Arabic/Unicode
    if payload_has_non_latin(payload):
        return jsonify({
            "status": "error",
            "message": "English only: Arabic and other non-Latin characters are not supported for PDF generation."
        }), 400

    # Build header replacements for template placeholders
    header_map = build_header(payload)

    # Build dynamic sections body
    sections_tex = build_sections_latex(payload)

    # Read LaTeX template (path relative to app root for Docker/CWD independence)
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.tex")
    with open(template_path, "r", encoding="utf-8") as f:
        tex = f.read()

    # Replace header placeholder (HEADER is built as complete LaTeX, don't escape again)
    header_content = header_map.get("HEADER", "")
    tex = tex.replace("{{HEADER}}", header_content)

    # Insert the body sections
    tex = tex.replace("{{SECTIONS}}", sections_tex)

    # Compile
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "cv.tex")
        pdf_path = os.path.join(tmpdir, "cv.pdf")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex)

        try:
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "cv.tex"],
                cwd=tmpdir,
                capture_output=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return jsonify({"status":"error","message":"LaTeX timeout","stderr": "Compilation timed out after 60s"}), 500
        except Exception as e:
            return jsonify({"status":"error","message": str(e),"stderr": ""}), 500

        # pdflatex often writes errors to stdout; merge both for diagnostics
        out = (result.stdout or b"").decode("utf-8", errors="replace")
        err = (result.stderr or b"").decode("utf-8", errors="replace")
        log = (out + "\n" + err).strip()
        if len(log) > 3000:
            log = "...\n" + log[-3000:]

        if result.returncode != 0:
            return jsonify({"status":"error","message":"LaTeX failed","stderr": log}), 500

        if not os.path.exists(pdf_path):
            return jsonify({"status":"error","message":"PDF not generated"}), 500

        return send_file(pdf_path, as_attachment=True, download_name="cv.pdf")

if __name__ == "__main__":
    # 0.0.0.0 so Docker/Railway can expose it; PORT from env for Railway
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=debug)
