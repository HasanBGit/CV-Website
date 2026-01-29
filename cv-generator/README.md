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
5. **Click "Generate PDF Resume"** to download your professional CV

## Project Structure

\`\`\`
cv-generator/
├── app.py                 # Flask backend with LaTeX generation
├── template.tex           # LaTeX template with professional formatting
├── templates/
│   └── index.html        # HTML interface with drag-and-drop
├── static/
│   └── style.css         # Modern, responsive styling
├── Dockerfile            # Docker setup with texlive-full
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Python dependencies
├── run.sh               # Quick start script
└── README.md            # This file
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
- The template uses placeholders like `{{FULL_NAME}}` and `{{SECTIONS}}`

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

The application is containerized and can be deployed to any platform supporting Docker:
- Railway
- Render
- AWS ECS
- Google Cloud Run
- DigitalOcean App Platform

Simply push the Docker image or connect your repository to these platforms.
