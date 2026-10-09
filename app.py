import html
import io
import re
import smtplib

from email.message import EmailMessage

import streamlit as st

from google import genai

from google.genai import types
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    ListFlowable,
    ListItem,
)
from xml.sax.saxutils import escape

from prompts import (

    SYSTEM_PROMPT,

    WELCOME_MESSAGE,

    SUMMARY_REQUEST_PROMPT,

)

# ============================================================

# CONFIGURATION

# ============================================================

MODEL_NAME = "gemini-3.5-flash"

MAX_IMAGE_SIZE_MB = 10

ALLOWED_IMAGE_TYPES = {"jpg", "jpeg", "png"}

st.set_page_config(

    page_title="Snap & Study",

    page_icon="📚",

    layout="centered",

)

# ============================================================

# PROFESSIONAL UI STYLING

# ============================================================

st.markdown(

    """

<style>

.stApp {

    background: linear-gradient(

        180deg, #f5f8ff 0%, #ffffff 48%, #f7f9fc 100%

    );

}

.block-container {

    max-width: 1000px;

    padding-top: 2rem;

    padding-bottom: 3rem;

}

h1, h2, h3 {

    color: #172554 !important;

    font-weight: 750 !important;

}

.stApp p {

    line-height: 1.7;

}

.stButton > button,

.stFormSubmitButton > button {

    border-radius: 12px;

    min-height: 44px;

    font-weight: 600;

    transition: all 0.2s ease;

}

.stFormSubmitButton > button[kind="primary"] {

    background: #2563eb;

    border: 1px solid #2563eb;

    color: white;

}

.stFormSubmitButton > button[kind="primary"]:hover {

    background: #1d4ed8;

    border-color: #1d4ed8;

}

.stTextArea textarea,

.stTextInput input {

    border-radius: 12px;

    border-color: #dbe4f0;

    background: white;

}

[data-testid="stFileUploader"] {

    background: white;

    border: 1px dashed #93b4eb;

    border-radius: 14px;

    padding: 12px;

}

[data-testid="stChatMessage"] {

    background: white;

    border: 1px solid #e5eaf3;

    border-radius: 16px;

    padding: 1rem;

    margin-bottom: 0.75rem;

    box-shadow: 0 3px 12px rgba(30, 58, 95, 0.04);

}

[data-testid="stExpander"] {

    background: white;

    border: 1px solid #e1e8f3;

    border-radius: 14px;

}

[data-testid="stForm"] {

    border: 1px solid #e1e8f3;

    border-radius: 16px;

    padding: 1.25rem;

    background: white;

}

hr {

    border-color: #e2e8f0;

}

.stCaption {

    color: #64748b;

}

</style>

""",

    unsafe_allow_html=True,

)

# ============================================================

# GMAIL SENDING FUNCTION

# ============================================================

def markdown_to_email_html(markdown_text: str) -> str:
    """Convert common Markdown into a safe, styled HTML email."""

    output = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    def format_inline(text: str) -> str:
        escaped = html.escape(text, quote=True)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", escaped)
        escaped = re.sub(r"`([^`]+?)`", r"<code>\1</code>", escaped)
        return escaped

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()

        if not line or line == "---":
            close_list()
            continue

        if line.startswith("### "):
            close_list()
            output.append(f"<h3>{format_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            close_list()
            output.append(f"<h2>{format_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            close_list()
            output.append(f"<h1>{format_inline(line[2:])}</h1>")
        elif line.startswith(("- ", "* ", "• ")):
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{format_inline(line[2:])}</li>")
        else:
            close_list()
            output.append(f"<p>{format_inline(line)}</p>")

    close_list()
    content_html = "\n".join(output)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:24px 12px;background:#f3f6fc;font-family:Arial,Helvetica,sans-serif;color:#243047;line-height:1.7;">
  <div style="max-width:680px;margin:0 auto;background:#ffffff;border:1px solid #e1e8f3;border-radius:14px;overflow:hidden;">
    <div style="background:#1e3a8a;padding:24px;color:#ffffff;">
      <h1 style="margin:0;font-size:25px;color:#ffffff;">📚 Snap &amp; Study</h1>
      <p style="margin:8px 0 0;color:#dbeafe;">Your personal study revision notes</p>
    </div>
    <div style="padding:24px;font-size:15px;overflow-wrap:anywhere;">
      <style>
        h1,h2,h3 {{ color:#1e3a8a; line-height:1.3; }}
        h2 {{ margin-top:26px; font-size:20px; }}
        h3 {{ margin-top:20px; font-size:17px; }}
        p {{ margin:10px 0; }}
        ul {{ padding-left:24px; }}
        li {{ margin:6px 0; }}
        code {{ background:#f1f5f9; padding:2px 5px; border-radius:4px; }}
      </style>
      {content_html}
    </div>
    <div style="padding:16px 24px;background:#f8fafc;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b;">
      Generated by Snap &amp; Study. Review important answers against your textbook.
    </div>
  </div>
</body>
</html>"""


def send_email(
    to_address: str,
    subject: str,
    body: str,
) -> None:
    """Send a formatted HTML email with a plain-text fallback."""

    gmail_address = st.secrets.get("GMAIL_ADDRESS", "").strip()
    app_password = (
        st.secrets.get("GMAIL_APP_PASSWORD", "")
        .replace(" ", "")
        .strip()
    )

    if not gmail_address or not app_password:
        raise ValueError(
            "Gmail credentials are missing. "
            "Check .streamlit/secrets.toml."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = gmail_address
    message["To"] = to_address
    message.set_content(body.strip())
    message.add_alternative(
        markdown_to_email_html(body.strip()),
        subtype="html",
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
        server.login(gmail_address, app_password)
        server.send_message(message)



def create_revision_pdf(markdown_text: str) -> bytes:
    """Create a downloadable PDF from a Markdown-style revision summary."""

    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Snap & Study Revision Summary",
        author="Snap & Study",
    )

    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SnapTitle",
        parent=base_styles["Title"],
        textColor=colors.HexColor("#1e3a8a"),
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "SnapHeading",
        parent=base_styles["Heading1"],
        textColor=colors.HexColor("#1e3a8a"),
        fontSize=16,
        leading=20,
        spaceBefore=14,
        spaceAfter=8,
    )
    subheading_style = ParagraphStyle(
        "SnapSubheading",
        parent=base_styles["Heading2"],
        textColor=colors.HexColor("#2563eb"),
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "SnapBody",
        parent=base_styles["BodyText"],
        fontSize=9.5,
        leading=14,
        spaceAfter=6,
    )

    story = [
        Paragraph("Snap &amp; Study", title_style),
        Paragraph("Study Revision Summary", subheading_style),
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#bfdbfe"),
            spaceAfter=14,
        ),
    ]

    bullet_items = []

    def flush_bullets():
        nonlocal bullet_items
        if bullet_items:
            story.append(
                ListFlowable(
                    [
                        ListItem(item, leftIndent=12)
                        for item in bullet_items
                    ],
                    bulletType="bullet",
                    leftIndent=18,
                    bulletFontName="Helvetica",
                    bulletFontSize=8,
                )
            )
            story.append(Spacer(1, 5))
            bullet_items = []

    def inline_markup(value: str) -> str:
        # Escape source text first, then support simple Markdown emphasis/code.
        safe = escape(value)
        safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
        safe = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", safe)
        safe = re.sub(r"`([^`]+?)`", r'<font name="Courier">\1</font>', safe)
        return safe

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()

        if not line or line == "---":
            flush_bullets()
            continue

        if line.startswith("### "):
            flush_bullets()
            story.append(Paragraph(inline_markup(line[4:]), subheading_style))
        elif line.startswith(("## ", "# ")):
            flush_bullets()
            heading_text = line[3:] if line.startswith("## ") else line[2:]
            story.append(Paragraph(inline_markup(heading_text), heading_style))
        elif line.startswith(("- ", "* ", "• ")):
            bullet_items.append(Paragraph(inline_markup(line[2:]), body_style))
        else:
            flush_bullets()
            story.append(Paragraph(inline_markup(line), body_style))

    flush_bullets()

    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
        canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(2 * cm, 1.0 * cm, "Generated by Snap & Study")
        canvas.drawRightString(A4[0] - 2 * cm, 1.0 * cm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )
    return buffer.getvalue()


# EMAIL VALIDATION

# ============================================================

def is_valid_email(address: str) -> bool:

    """Perform basic recipient email validation."""

    if not address or len(address) > 254:

        return False

    if address.count("@") != 1 or any(

        character.isspace() for character in address

    ):

        return False

    local, domain = address.rsplit("@", 1)

    return (

        bool(local)

        and bool(domain)

        and "." in domain

        and not domain.startswith(".")

        and not domain.endswith(".")

    )

# ============================================================

# GEMINI CLIENT

# ============================================================

@st.cache_resource

def get_gemini_client(api_key: str):

    """Create and reuse the Gemini API client."""

    return genai.Client(api_key=api_key)

def initialize_chat():

    """Initialize chat history and session state."""

    if "messages" not in st.session_state:

        st.session_state.messages = []

    if "chat" not in st.session_state:

        api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

        if not api_key or api_key == "YOUR_ACTUAL_API_KEY":

            st.error(

                "Gemini API key is missing. Add it to "

                ".streamlit/secrets.toml."

            )

            st.stop()

        client = get_gemini_client(api_key)

        st.session_state.chat = client.chats.create(

            model=MODEL_NAME,

            config=types.GenerateContentConfig(

                system_instruction=SYSTEM_PROMPT,

            ),

        )

st.markdown("# 📚 Snap & Study")

st.markdown("### Upload. Understand. Learn.")

st.write(

    "Turn textbook photos into clear explanations "

    "and exam-ready revision notes."

)

st.markdown(

    "📷 Image understanding  ·  "

    "🤖 AI explanations  ·  "

    "✉️ Email revision notes"

)

st.divider()

# ============================================================

# INITIALIZE APPLICATION

# ============================================================

try:

    initialize_chat()

except Exception:

    st.error(

        "Unable to initialize Gemini. Check your API key, "

        "internet connection, and model availability."

    )

    st.stop()

# ============================================================

# CONVERSATION HISTORY

# ============================================================

st.markdown("### 💬 Your study conversation")

if not st.session_state.messages:

    with st.chat_message("assistant"):

        st.markdown(WELCOME_MESSAGE)

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# ============================================================

# EMAIL STUDY SUMMARY

# ============================================================

has_assistant_messages = any(

    message["role"] == "assistant"

    for message in st.session_state.messages

)

if has_assistant_messages:

    with st.expander("📧 Email your study summary"):

        st.caption(

            "Create a revision summary of your study session "

            "and send it to an email inbox."

        )

        with st.form("email_study_summary_form"):

            recipient_email = st.text_input(

                "Recipient email address",

                placeholder="student@example.com",

            )

            email_submitted = st.form_submit_button(

                "✉️ Send study summary by email",

                type="primary",

                use_container_width=True,

            )

        if email_submitted:

            recipient_email = recipient_email.strip()

            if not is_valid_email(recipient_email):

                st.warning(

                    "Please enter a valid recipient email address."

                )

            else:

                try:

                    with st.spinner(

                        "Preparing your study summary..."

                    ):

                        summary_response = (

                            st.session_state.chat.send_message(

                                SUMMARY_REQUEST_PROMPT

                            )

                        )

                        summary = summary_response.text

                    if not summary or not summary.strip():

                        st.error(

                            "Gemini returned an empty summary. "

                            "Please try again."

                        )

                    else:

                        with st.spinner("Sending your email..."):

                            send_email(

                                recipient_email,

                                "Your Snap & Study Revision Summary",

                                summary.strip(),

                            )

                        st.success(

                            "Study summary sent successfully! "

                            f"Recipient: {recipient_email}"

                        )

                except ValueError as error:

                    st.error(str(error))

                except smtplib.SMTPAuthenticationError:

                    st.error(

                        "Gmail authentication failed. Verify your "

                        "Gmail address and App Password in "

                        ".streamlit/secrets.toml."

                    )

                except smtplib.SMTPException:

                    st.error(

                        "Gmail could not send the email. "

                        "Check your Gmail settings and try again."

                    )

                except (OSError, TimeoutError):

                    st.error(

                        "A network error occurred. "

                        "Check your internet connection and retry."

                    )

                except Exception:

                    st.error(

                        "Unable to generate or send the summary. "

                        "Check your Gemini configuration and retry."

                    )

# ============================================================

# PDF REVISION SUMMARY DOWNLOAD
# ============================================================

if has_assistant_messages:
    with st.expander("📄 Download revision summary as PDF"):
        st.caption(
            "Generate a printable revision sheet from this study conversation."
        )

        if st.button(
            "Create PDF revision summary",
            key="create_revision_pdf",
            use_container_width=True,
        ):
            try:
                with st.spinner("Preparing your revision summary..."):
                    pdf_summary_response = (
                        st.session_state.chat.send_message(
                            SUMMARY_REQUEST_PROMPT
                        )
                    )
                    pdf_summary = pdf_summary_response.text

                if not pdf_summary or not pdf_summary.strip():
                    st.error(
                        "Gemini returned an empty summary. Please try again."
                    )
                else:
                    st.session_state.pdf_revision_summary = pdf_summary.strip()
                    st.success("Your revision summary is ready to download.")

            except Exception:
                st.error(
                    "Unable to generate the PDF summary. "
                    "Check your Gemini connection and try again."
                )

        saved_pdf_summary = st.session_state.get("pdf_revision_summary")

        if saved_pdf_summary:
            try:
                pdf_bytes = create_revision_pdf(saved_pdf_summary)
                st.download_button(
                    label="⬇️ Download revision summary (PDF)",
                    data=pdf_bytes,
                    file_name="snap_and_study_revision_summary.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_revision_pdf",
                )
            except Exception:
                st.error(
                    "Unable to create the PDF file. Please try again."
                )


# STUDY INPUT FORM

# ============================================================

st.markdown("### 📖 Start a study session")

st.caption(

    "Upload a textbook image, type a question, "

    "or do both for a more detailed explanation."

)

with st.form("study_form", clear_on_submit=True):

    uploaded_image = st.file_uploader(

        "Upload a study image (optional)",

        type=sorted(ALLOWED_IMAGE_TYPES),

        help=(

            "Supported formats: JPG, JPEG, PNG. "

            "Maximum size: 10 MB."

        ),

    )

    question = st.text_area(

        "Your question",

        placeholder=(

            "Example: Explain this diagram or solve "

            "question 5 step by step."

        ),

        max_chars=4000,

    )

    submitted = st.form_submit_button(

        "✨ Ask Snap & Study",

        type="primary",

        use_container_width=True,

    )

# ============================================================

# PROCESS STUDY REQUEST

# ============================================================

if submitted:

    question = question.strip()

    if not question and uploaded_image is None:

        st.warning("Enter a question or upload an image.")

    elif (

        uploaded_image is not None

        and uploaded_image.size > MAX_IMAGE_SIZE_MB * 1024 * 1024

    ):

        st.error(

            f"Image is too large. Maximum size is "

            f"{MAX_IMAGE_SIZE_MB} MB."

        )

    else:

        prompt = question or (

            "Explain the uploaded study material in simple English. "

            "Identify the topic and highlight important exam points."

        )

        parts = []

        if uploaded_image is not None:

            parts.append(

                types.Part.from_bytes(

                    data=uploaded_image.getvalue(),

                    mime_type=uploaded_image.type,

                )

            )

        parts.append(prompt)

        with st.spinner(

            "📚 Snap & Study is preparing your explanation..."

        ):

            try:

                response = st.session_state.chat.send_message(parts)

                answer = response.text

                if not answer:

                    st.error(

                        "Gemini returned an empty response. "

                        "Please try another question."

                    )

                else:

                    st.session_state.messages.extend([

                        {"role": "user", "content": prompt},

                        {"role": "assistant", "content": answer},

                    ])

                    st.rerun()

            except Exception:

                st.error(

                    "Gemini request failed. Check your connection "

                    "and model availability, then try again."

                )

# ============================================================

# FOOTER AND CLEAR CONVERSATION

# ============================================================

st.divider()

st.caption(

    "📚 Snap & Study · Learn smarter, one question at a time."

)

st.caption(

    "AI-generated explanations may contain errors. "

    "Verify important academic answers with your study materials."

)

if st.button(

    "🗑️ Clear conversation",

    use_container_width=True,

):

    st.session_state.messages = []

    st.session_state.pop("chat", None)

    st.rerun()
