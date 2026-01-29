from flask import Flask, request, send_file, render_template, jsonify
import subprocess, tempfile, os, textwrap

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

def bullets_to_items(bullets):
    if not bullets: return ""
    lines = []
    for b in bullets:
        if not b: continue
        lines.append(rf"\resumeItem{{{esc(b)}}}")
    return "\n".join(lines)

def make_subheading(title, dates, org, location):
    return textwrap.dedent(rf"""
    \resumeSubheading
      {{{esc(title)}}}{{{esc(dates)}}}
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
            out.append(r"\resumeSubHeadingList")
            out.append(bullets_to_items(x["bullets"]))
            out.append(r"\resumeSubHeadingListEnd")
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
            # Make project name a clickable link
            name = rf"\href{{{link}}}{{{name}}}"
        out.append(make_subheading(name, p.get("dates",""), p.get("description",""), ""))  # 4th column empty
        if p.get("bullets"):
            out.append(r"\resumeSubHeadingList")
            out.append(bullets_to_items(p["bullets"]))
            out.append(r"\resumeSubHeadingListEnd")
    out.append(r"\resumeSubHeadingListEnd")
    return "\n".join(out)

def build_publications(data):
    # data: list of {title, date, publisher, bullets: []}
    if not data: return ""
    out = [r"\resumeSubHeadingList"]
    for p in data:
        out.append(make_subheading(p.get("title",""), p.get("date",""), p.get("publisher",""), ""))
        if p.get("bullets"):
            out.append(r"\resumeSubHeadingList")
            out.append(bullets_to_items(p["bullets"]))
            out.append(r"\resumeSubHeadingListEnd")
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

def build_custom_sections(custom_sections):
    # custom_sections: [{title, blocks:[{title, dates, org, location, bullets:[]}] }]
    if not custom_sections: return ""
    out = []
    for sec in custom_sections:
        title = sec.get("title","Custom")
        out.append(f"\\vspace{{0.5ex}}\n\\section{{{esc(title)}}}")
        out.append(r"\resumeSubHeadingList")
        for b in sec.get("blocks", []):
            out.append(make_subheading(b.get("title",""), b.get("dates",""), b.get("org",""), b.get("location","")))
            if b.get("bullets"):
                out.append(r"\resumeSubHeadingList")
                out.append(bullets_to_items(b["bullets"]))
                out.append(r"\resumeSubHeadingListEnd")
        out.append(r"\resumeSubHeadingListEnd")
        out.append("")  # spacer
    return "\n".join(out)

def build_header(u):
    # Header is a fixed center block in the template, we fill placeholders
    # We return replacements for {{FULL_NAME}}, {{PHONE}}, etc.
    header_data = {
        "FULL_NAME": u.get("name",""),
        "PHONE": u.get("phone",""),
        "EMAIL": u.get("email",""),
        "LINKEDIN": u.get("linkedin",""),
        "GITHUB": u.get("github",""),
        "WEBSITE": u.get("website",""),
        "SUMMARY": u.get("summary",""),
    }
    
    # Initialize custom headers with empty values
    for i in range(1, 4):
        header_data[f"CUSTOM_HEADER_{i}_LABEL"] = ""
        header_data[f"CUSTOM_HEADER_{i}_VALUE"] = ""
    
    # Add custom headers
    custom_headers = u.get("custom_headers", [])
    for i, header in enumerate(custom_headers[:3]):  # Limit to 3 headers
        label = header.get("label", "")
        value = header.get("value", "")
        if label and value:
            header_data[f"CUSTOM_HEADER_{i+1}_LABEL"] = label
            header_data[f"CUSTOM_HEADER_{i+1}_VALUE"] = value
    
    return header_data

# Map section names (as shown in UI) to builders
SECTION_BUILDERS = {
    "Summary": lambda d: f"\\vspace{{0.5ex}}\n\\section*{{Summary}}\n{esc(d.get('summary',''))}\n",
    "Education": lambda d: f"\\vspace{{0.5ex}}\n\\section{{Education}}\n{build_education(d.get('education'))}\n",
    "Experience": lambda d: f"\\vspace{{0.5ex}}\n\\section{{Experience}}\n{build_experience(d.get('experience'))}\n",
    "Projects": lambda d: f"\\vspace{{0.5ex}}\n\\section{{Projects}}\n{build_projects(d.get('projects'))}\n",
    "Skills": lambda d: f"\\vspace{{0.5ex}}\n\\section{{Skills}}\n{build_skills(d.get('skills'))}\n",
    "Certifications": lambda d: f"\\vspace{{0.5ex}}\n\\section{{Certifications}}\n{build_certifications(d.get('certifications'))}\n",
    "Publications": lambda d: f"\\vspace{{0.5ex}}\n\\section{{Publications}}\n{build_publications(d.get('publications'))}\n",
}

DEFAULT_ORDER = [
    "Summary", "Education", "Experience", "Projects", "Skills", "Certifications", "Publications"
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

@app.route("/generate-cv", methods=["POST"])
def generate_cv():
    payload = request.get_json(force=True)

    # Build header replacements for template placeholders
    header_map = build_header(payload)

    # Build dynamic sections body
    sections_tex = build_sections_latex(payload)

    # Read LaTeX template with preserved preamble/macros
    with open("template.tex", "r", encoding="utf-8") as f:
        tex = f.read()

    # Replace header placeholders
    for k, v in header_map.items():
        tex = tex.replace(f"{{{{{k}}}}}", esc(v))

    # Insert the body sections
    tex = tex.replace("{{SECTIONS}}", sections_tex)

    # Compile
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "cv.tex")
        pdf_path = os.path.join(tmpdir, "cv.pdf")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex)

        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "cv.tex"],
                cwd=tmpdir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            return jsonify({"status":"error","message":"LaTeX failed","stderr": e.stderr.decode(errors="ignore")}), 500

        if not os.path.exists(pdf_path):
            return jsonify({"status":"error","message":"PDF not generated"}), 500

        return send_file(pdf_path, as_attachment=True, download_name="cv.pdf")

if __name__ == "__main__":
    # 0.0.0.0 so Docker can expose it
    app.run(host="0.0.0.0", port=5000, debug=True)
