#!/usr/bin/env python3

import tempfile
import os
import subprocess
import sys

# Add the current directory to Python path
sys.path.insert(0, '.')

from app import build_header, build_sections_latex

def test_cv_generation():
    # Test data
    test_data = {
        'name': 'John Doe',
        'phone': '123-456-7890',
        'email': 'john@example.com',
        'linkedin': 'https://linkedin.com/in/johndoe',
        'github': 'https://github.com/johndoe',
        'website': 'https://johndoe.com',
        'summary': 'Test summary for CV generation',
        'education': [{
            'university': 'Test University', 
            'degree': 'BS Computer Science', 
            'date': '2020', 
            'location': 'Test City'
        }],
        'experience': [],
        'projects': [],
        'publications': [],
        'skills': {'Programming': ['Python', 'JavaScript']},
        'certifications': []
    }

    print("Building header and sections...")
    
    # Build header and sections
    header_map = build_header(test_data)
    sections_tex = build_sections_latex(test_data)
    
    print("Header map:", header_map)
    print("Sections tex length:", len(sections_tex))
    
    # Read template
    with open('template.tex', 'r', encoding='utf-8') as f:
        tex = f.read()
    
    print("Template loaded, length:", len(tex))
    
    # Replace placeholders
    for k, v in header_map.items():
        tex = tex.replace(f'{{{{{k}}}}}', v)
    
    # Insert sections
    tex = tex.replace('{{SECTIONS}}', sections_tex)
    
    print("Template processed")
    
    # Write test file
    with open('test_cv.tex', 'w', encoding='utf-8') as f:
        f.write(tex)
    
    print("Test LaTeX file created: test_cv.tex")
    
    # Try to compile
    try:
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', 'test_cv.tex'],
            cwd='.',
            check=True,
            capture_output=True,
            text=True
        )
        print("LaTeX compilation successful!")
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if os.path.exists('test_cv.pdf'):
            print("PDF file created successfully!")
            return True
        else:
            print("PDF file not found after compilation")
            return False
            
    except subprocess.CalledProcessError as e:
        print("LaTeX compilation failed!")
        print("Return code:", e.returncode)
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

if __name__ == "__main__":
    test_cv_generation()
