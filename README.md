# AI Talent Scouting & Engagement Agent

## 🚀 Working Prototype

This is an AI-powered recruitment assistant that:
- Parses Job Descriptions
- Matches candidates
- Simulates candidate interest
- Generates Match Score and Interest Score
- Produces a ranked shortlist

---

## 🖥️ How to Run the Project

### 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/ai-talent-agent.git
cd ai-talent-agent

### 2. Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Set API Key
setx OPENAI_API_KEY "your_api_key"

Restart terminal after this step.

### 5. Run backend
python app.py

### 6. Run frontend
streamlit run ui.py

### 7. Open in browser
http://localhost:8501

---

## ⚙️ Features

- Job Description parsing
- Candidate matching (Match Score)
- Interest prediction (Interest Score)
- Final ranking
- Skill gap analysis
- Explainable results