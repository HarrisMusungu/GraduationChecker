import re

import fitz  # PyMuPDF for PDF processing
from flask import Flask, flash, render_template, request

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def extract_text_from_pdf(file_stream):
    try:
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text("text")
        return text
    except Exception as e:
        flash(f'An error occurred while processing the PDF: {e}')
        return None

def parse_credit_summary(transcript_text):
    credit_summary = {}
    pattern = re.compile(
        r'(American History|Economics|Elective|English|Fine Arts|Foreign Language|Health|Math|Physical Education|Principles of Democracy|Science|World History)\s+'
        r'(\d+\.\d+)\s+(\d+\.\d+)')
    
    matches = pattern.findall(transcript_text)
    if not matches:
        flash('No credit summary section found or the pattern did not match.')
        return None
    
    for match in matches:
        category, _, earned = match
        credit_summary[category] = float(earned)
    
    return credit_summary

def check_graduation_requirements(credit_summary):
    required_credits = {
        "English": 4,
        "Math": 4,
        "Science": 3,
        "Social Studies": 3,
        "Health": 0.5,
        "Economics": 0.5,
        "Physical Education": 0.5,
        "Fine Arts": 1,
        "Elective": 3.5,
    }
    
    credits_needed = {category: required for category, required in required_credits.items()}
    social_studies_courses = ['Social Studies', 'American History', 'World History', 'Principles of Democracy']
    social_studies_credits = sum(credit_summary.get(course, 0) for course in social_studies_courses)
    credit_summary['Social Studies'] = social_studies_credits
    
    for category in credit_summary:
        if category in credits_needed:
            credits_needed[category] = max(0, required_credits[category] - credit_summary[category])
    
    return credits_needed, credit_summary

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    required_credits = {
        "English": 4,
        "Math": 4,
        "Science": 3,
        "Social Studies": 3,
        "Health": 0.5,
        "Economics": 0.5,
        "Physical Education": 0.5,
        "Fine Arts": 1,
        "Elective": 3.5,
    }

    if request.method == 'POST':
        pdf_file = request.files.get('transcript')
        if pdf_file:
            transcript_text = extract_text_from_pdf(pdf_file)
            if transcript_text is None:
                return render_template('upload.html', error="Failed to process PDF.")
            
            credit_summary = parse_credit_summary(transcript_text)
            if credit_summary is None:
                return render_template('upload.html', error="Failed to parse the credit summary.")
            
            credits_needed, earned_credits = check_graduation_requirements(credit_summary)
            return render_template(
                'results.html',
                earned_credits=earned_credits,
                credits_needed=credits_needed,
                required_credits=required_credits  # Pass this variable to the template
            )
        else:
            flash('Please select a file to upload.')
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)

