# 📚 Snap & Study — AI-Powered Study Assistant

**Upload. Understand. Learn.**

Snap & Study is an AI-powered learning assistant that helps students understand textbook content, clarify doubts, and prepare exam-ready revision notes. By combining image understanding with conversational AI, it transforms textbook photos, handwritten notes, questions, and diagrams into clear, easy-to-understand explanations.

🔗 **Live Demo:** https://snap-and-study-assistant.streamlit.app/

💻 **GitHub Repository:** https://github.com/Suhas2811/snap-and-study

---

## ✨ Key Features

- **🖼️ Image Understanding:** Upload textbook photos, notes, questions, and diagrams for AI-powered explanations.
- **🤖 AI-Powered Learning:** Ask questions and receive explanations in simple English.
- **📝 Revision Notes:** Generate structured, exam-oriented revision summaries to support study and revision.
- **📧 Email Revision Summaries:** Send formatted revision notes directly to an email address.
- **📄 PDF Downloads:** Generate downloadable PDF documents containing revision summaries.
- **💬 Interactive Study Sessions:** Ask follow-up questions to explore concepts in greater detail.
- **🎨 User-Friendly Interface:** A clean, intuitive interface built with Streamlit.

## 🎯 Problem Statement

Students often spend significant time understanding complex textbook concepts, interpreting diagrams, and preparing revision notes. Traditional study methods can make it difficult to turn lengthy material into concise, understandable explanations.

Snap & Study addresses this challenge by providing an interactive AI-assisted learning experience that helps students understand study material and organize their revision content more efficiently.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web application |
| Google Gemini API | AI-powered text and image understanding |
| ReportLab | PDF generation |
| Gmail SMTP | Email delivery of revision summaries |
| Git and GitHub | Version control and source code hosting |
| Streamlit Community Cloud | Application deployment |

## ⚙️ How It Works

1. Open the live application.
2. Upload a study image, type a question, or do both.
3. Submit your input to receive an AI-generated explanation.
4. Review the explanation and ask follow-up questions.
5. Generate a revision summary.
6. Download the summary as a PDF or send it through email.

## 🚀 Run Locally

### Prerequisites

- Python 3.12 or a compatible Python version
- Git
- A Google Gemini API key
- Gmail credentials configured for app-password access if you want to use the email feature

### 1. Clone the repository

```bash
git clone https://github.com/Suhas2811/snap-and-study.git
cd snap-and-study
```

### 2. Create a virtual environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks environment activation, use Command Prompt and run:

```bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure secrets

Create a folder named `.streamlit` in the project root if it does not already exist. Inside it, create a file named `secrets.toml`.

Add your credentials using the following format:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
GMAIL_ADDRESS = "your_gmail_address"
GMAIL_APP_PASSWORD = "your_gmail_app_password"
```

Replace the placeholder values with your own credentials. Use a Gmail App Password where required for SMTP access.

**Security:** Never commit API keys, email passwords, or other secrets to GitHub. The `.streamlit/secrets.toml` file is excluded through `.gitignore`.

### 5. Start the application

```bash
streamlit run app.py
```

Streamlit will provide a local URL, usually `http://localhost:8501`, where you can access the application.

## 🔐 Configuration and Deployment

The application uses Streamlit secrets to manage sensitive configuration values.

For deployment on Streamlit Community Cloud:

1. Connect the GitHub repository to Streamlit Community Cloud.
2. Select the `main` branch and `app.py` as the main file.
3. Add the required credentials in the app's **Settings → Secrets** configuration.
4. Deploy the application and test its features.

Keep all credentials private and never place them directly in source code.

## 📁 Project Structure

```text
snap-and-study/
├── .streamlit/
│   └── secrets.toml       # Local secrets (not committed)
├── app.py                 # Main Streamlit application
├── prompts.py             # AI prompts and welcome messages
├── requirements.txt       # Python dependencies
├── .gitignore             # Excludes secrets and generated files
└── README.md              # Project documentation
```

## 🌟 Future Enhancements

- Support for multiple document formats, including PDF and DOCX.
- Conversation history and personalized study sessions.
- Automatic generation of quizzes and practice tests.
- Flashcards and spaced-repetition revision tools.
- Support for multiple languages.
- More advanced organization of notes by subject and topic.

## 🎓 Intended Audience

Snap & Study is designed for students, learners, and anyone who wants to understand educational material more easily and prepare organized revision notes.

## 👨‍💻 Author

**Suhas Subramani**

GitHub: [@Suhas2811](https://github.com/Suhas2811)

## 📄 License

This project is available for educational and learning purposes. A formal open-source license can be added to define permissions for reuse, modification, and distribution.

---

**Made with Python, Streamlit, and Google Gemini AI. 📚**