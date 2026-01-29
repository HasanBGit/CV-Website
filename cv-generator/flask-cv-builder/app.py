from flask import Flask, send_file
import subprocess
import tempfile
import os

app = Flask(__name__)

@app.route("/generate-cv", methods=["GET"])
def generate_cv():
    # Dummy user data for testing (later you can pass from a form/JSON)
    user_data = {
        "FULL_NAME": "Hassan Barmandah",
        "PHONE": "+966580586649",
        "EMAIL": "hassan@example.com",
        "LINKEDIN": "linkedin.com/in/hassan",
        "GITHUB": "github.com/hassan",
        "WEBSITE": "hassan.dev",
        "SUMMARY": "Software Engineer focused on Artificial Intelligence...",
        "UNIVERSITY": "Umm Al-Qura University",
        "LOCATION": "Makkah, Saudi Arabia",
        "DEGREE": "B.S. in Software Engineering, GPA: 3.91/4.00",
        "DATE": "Expected Graduation: June 2027",
        "EXPERIENCE_BLOCKS": r"""
\resumeSubheading{Data Analyst Intern}{Jul 2025 -- Aug 2025}{Uptrail}{London Area, UK (Remote)}
\resumeSubHeadingList
    \resumeItem{Participated in structured training, working on real-world data analysis projects}
    \resumeItem{Utilized Python, SQL, Power BI, and Tableau for insights}
\resumeSubHeadingListEnd
""",
        "PROJECT_BLOCKS": r"""
\resumeSubheading{ModelCraft}{Jul 2025 -- Present}{Open-Source Repository}{}
\resumeSubHeadingList
    \resumeItem{Built an open-source repository covering ML and DL architectures}
\resumeSubHeadingListEnd
""",
        "PUBLICATION_BLOCKS": r"""
\resumeSubheading{Saudi-Dialect-ALLaM: LoRA Fine-Tuning for Dialectal Arabic Generation}{Aug 2025}{arXiv}{}
\resumeSubHeadingList
    \resumeItem{Fine-tuned ALLaM-7B-Instruct for Saudi dialect generation}
\resumeSubHeadingListEnd
""",
        "SKILLS": r"""
\resumeItem{\textbf{Programming Languages}: Python, Java, SQL, HTML, CSS, JavaScript, React, Spring Boot}
\resumeItem{\textbf{Data Science \& ML}: Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn, PyTorch, OpenCV, Jupyter Notebook}
\resumeItem{\textbf{Interpersonal Skills}: Leadership, Teamwork, Communication, Problem Solving}
""",
        "CERTIFICATION_BLOCKS": r"""
\resumeSubheading{Deep Learning Specialization}{Jul 2025}{DeepLearning.AI}{}
\resumeSubheading{AWS AI Practitioner}{May 2025 -- May 2028}{Amazon Web Services (AWS)}{}
"""
    }

    # Read LaTeX template
    with open("template.tex", "r", encoding="utf-8") as f:
        tex = f.read()

    # Replace placeholders {{KEY}}
    for key, value in user_data.items():
        tex = tex.replace(f"{{{{{key}}}}}", value)

    # Create a temporary folder for build
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "cv.tex")
        pdf_path = os.path.join(tmpdir, "cv.pdf")

        # Write filled LaTeX file
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex)

        # Compile LaTeX → PDF
        LATEX_PATH = r"C:\Users\ksah2\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"

        try:
            result = subprocess.run(
                [LATEX_PATH, "-interaction=nonstopmode", "cv.tex"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ PDF generated successfully!")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print("❌ LaTeX compilation failed!")
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
            return f"Error compiling LaTeX. Check logs."

        # Return PDF file
        return send_file(pdf_path, as_attachment=True, download_name="cv.pdf")

if __name__ == "__main__":
    print("🚀 Flask server running at http://127.0.0.1:5000/generate-cv")
    app.run(debug=True)
