# Professional CV Generator

A Flask web application that generates professional PDF resumes using HTML/CSS/JS frontend and LaTeX compilation in Docker.

## Features

- **Interactive Web Interface**: Clean, modern form with drag-and-drop section ordering
- **Dynamic Sections**: Add multiple entries for experience, education, projects, publications, certifications
- **Custom Sections**: Create custom sections like "Volunteering", "Awards", etc.
- **Drag & Drop Ordering**: Reorder resume sections by dragging chips
- **LaTeX Compilation**: Professional PDF generation with proper formatting
- **Docker Integration**: Optimized LaTeX installation (only necessary packages, ~500MB vs 4GB)
- **ATS Friendly**: Generated PDFs are machine-readable and ATS-compatible

## Quick Start

### Prerequisites
- Docker and Docker Compose installed

### Setup & Run

1. **Clone/Download the project files**

2. **Build and start the application:**
   \`\`\`bash
   docker-compose build
   docker-compose up
   \`\`\`

3. **Open your browser:**
   \`\`\`
   http://localhost:5000
   \`\`\`

### Usage

1. **Fill in your information** in the web form
2. **Add entries** for experience, education, projects, etc.
3. **Drag and drop** the section chips to reorder your resume
4. **Add custom sections** if needed (volunteering, awards, etc.)
5. **Click "Download CV (PDF)"** to download your professional CV

## Project Structure

\`\`\`
.
├── app.py                 # Flask backend with LaTeX generation
├── template.tex           # LaTeX template with professional formatting
├── example_cv.json        # Sample CV data for /api/example-cv
├── templates/
│   └── index.html         # HTML interface with drag-and-drop
├── static/
│   └── style.css         # Modern, responsive styling
├── Dockerfile            # Docker setup with LaTeX
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Python dependencies
├── run.sh                # Quick start script
├── .gitignore            # Ignores test artifacts, __pycache__, venv, etc.
└── README.md             # This file
\`\`\`

## How It Works

1. **Frontend**: Users fill out a comprehensive HTML form with drag-and-drop section ordering
2. **Data Collection**: JavaScript collects all form data into a structured JSON payload
3. **Backend Processing**: Flask receives the JSON and builds LaTeX code with proper escaping
4. **PDF Generation**: LaTeX is compiled to PDF using pdflatex in the Docker container
5. **Download**: The generated PDF is returned as a download to the user

## Customization

### Adding New Section Types
1. Add a new builder function in `app.py`
2. Add it to the `SECTION_BUILDERS` dictionary
3. Update the frontend to include the new section type

### Modifying LaTeX Template
- Edit `template.tex` to change formatting, fonts, or layout
- The template uses placeholders `{{HEADER}}` and `{{SECTIONS}}`

### Styling Changes
- Modify `static/style.css` to change the web interface appearance
- The design uses a modern gradient theme with responsive layout
- All JavaScript is embedded in the HTML template for simplicity

## Technical Details

- **Backend**: Flask with comprehensive LaTeX character escaping
- **Frontend**: Vanilla JavaScript with drag-and-drop API
- **PDF Generation**: pdflatex with optimized LaTeX package selection
- **Docker**: Ensures consistent LaTeX environment across deployments
- **Responsive Design**: Works on desktop and mobile devices

## Deployment

**Vercel is not suitable** for this app: it runs a Flask server and compiles LaTeX (pdflatex) to PDF. Vercel does not support Docker or long-running processes and has no LaTeX runtime.

Deploy to a platform that supports **Docker** or **long-running web servers**:

| Platform        | Notes                                      |
|-----------------|--------------------------------------------|
| **Railway**     | Connect repo, use Dockerfile; free tier OK |
| **Render**      | Web Service, Docker; free tier available   |
| **Fly.io**      | Docker; free tier available                |
| **Google Cloud Run** | Docker; pay per use                   |
| **DigitalOcean App Platform** | Docker                        |

1. Push your repo to GitHub.
2. Create a new Web Service / App and connect the repo.
3. Set build to use the **Dockerfile** (no need to set a custom build command).
4. Expose port **5000** and set the start command to the default (e.g. `python app.py` or use the Dockerfile `CMD`).

The first Docker build may take several minutes (LaTeX install). Later builds are cached and faster.
