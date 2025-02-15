import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
from dotenv import load_dotenv
import re
import plotly.graph_objects as go
from textblob import TextBlob

# Load API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    return text

# Function to extract percentage from AI response
def extract_percentage(text):
    match = re.search(r'Score: (\d+)%', text)  # Look for "Score: XX%"
    if match:
        return int(match.group(1))  # Convert to integer
    return None  # Default if no percentage found

# Function to analyze spelling & grammar
def analyze_text_quality(text):
    blob = TextBlob(text)
    errors = len(blob.correct().split()) - len(text.split())  # Count spelling errors
    error_rate = max(0, 100 - (errors * 2))  # Convert errors to a score
    return min(100, error_rate)  # Ensure the score is within 0-100%

# Function to analyze resume using Google Gemini
def score_resume(job_description, resume_text):
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    You are an AI resume evaluator. Compare the following resume against the job description and provide:
    
    1. **A numerical match score** (0-100%) in this format: `Score: XX%`
    2. **A brief explanation** of why the resume received this score.
    3. **Feedback on resume style** (formatting, structure, clarity).
    4. **Suggestions** on how the candidate can improve their resume.

    ### Job Description ###
    {job_description}

    ### Resume ###
    {resume_text}

    ### Output Format ###
    - Score: XX%
    - Explanation: (Brief reasoning about the match)
    - Style Feedback: (Feedback on formatting, readability, and clarity)
    - Suggestions: (How to improve the resume)
    """

    response = model.generate_content(prompt, generation_config={"temperature": 0})  # Set temperature to 0 for consistency
    
    return response.text  # Extract text response

# Function to create a circular progress bar
def circular_progress_bar(score, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': title},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}}
    ))
    return fig

# Streamlit UI
st.title("📄 AI Resume Screener")
st.markdown("### Analyze your resume's match, content quality, and style with AI!")
st.write("Upload your resume and enter a job description to see how well they match!")

# Job Description Input
job_description = st.text_area("Enter Job Description", height=200)

# Resume Upload
uploaded_file = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])

if uploaded_file and job_description:
    resume_text = extract_text_from_pdf(uploaded_file)
    
    with st.spinner("Analyzing..."):
        result = score_resume(job_description, resume_text)

    # Extract percentage score
    match_score = extract_percentage(result)

    # Analyze spelling & grammar
    grammar_score = analyze_text_quality(resume_text)

    # Display AI Score, Explanation, and Suggestions
    st.subheader("🔍 Resume Match Analysis")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        if match_score is not None:
            st.plotly_chart(circular_progress_bar(match_score, "Match Score", "green"))
    
    with col2:
        st.plotly_chart(circular_progress_bar(grammar_score, "Content Quality", "blue"))
    
    with col3:
        st.plotly_chart(circular_progress_bar(80, "Style & Formatting", "purple"))  # Placeholder

    st.subheader("📋 AI Feedback")
    st.write(result)  # Display AI-generated explanation and suggestions
