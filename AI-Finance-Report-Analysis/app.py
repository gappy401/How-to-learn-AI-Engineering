import os
import fitz  # PyMuPDF
import streamlit as st
from langchain_groq import ChatGroq

# --- 1. Configure API Key ---
if "GROQ_API_KEY" not in os.environ:
    st.sidebar.title("Configuration")
    api_key = st.sidebar.text_input("Enter your GROQ API Key", type="password")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    else:
        st.warning("Please enter your GROQ API Key to proceed.")
        st.stop()

# --- 2. Initialize Groq LLM ---
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)

# --- 3. PDF Extraction ---
@st.cache_data
def extract_text_from_pdf(uploaded_file):
    if uploaded_file is None:
        return ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        return "\n".join([page.get_text("text") for page in doc])

# --- 4. Summarize ---
def summarize_report(text: str) -> str:
    prompt = f"""
    You are a financial analyst.
    Summarize the key revenue trends, growth drivers, risks, and forward guidance for stakeholders.
    Be concise and structured with bullet points.

    Report (first 4000 chars):
    {text[:4000]}
    """
    return llm.invoke(prompt).content

# --- 5. Q&A ---
def answer_question(text: str, question: str) -> str:
    prompt = f"""
    You are a financial analyst. Use the report to answer the question precisely.
    If the information isn't present, say so rather than guessing.

    Question: {question}

    Report (first 4000 chars):
    {text[:4000]}
    """
    return llm.invoke(prompt).content

# --- 6. Streamlit UI ---
st.title("📊 Financial Report Analyzer")
st.markdown("Upload a PDF and chat with the AI analyst about revenue trends, risks, and guidance.")

uploaded_file = st.file_uploader("Upload Financial Report PDF", type="pdf")

if uploaded_file:
    report_text = extract_text_from_pdf(uploaded_file)
    st.success(f"PDF uploaded and {len(report_text)} characters extracted.")

    # Show executive summary immediately
    st.subheader("Executive Summary")
    st.markdown(summarize_report(report_text))

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about the report (e.g., 'Summarize revenue trends')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing report..."):
                response = answer_question(report_text, prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    # Optional: show raw text
    with st.expander("View Extracted PDF Text"):
        st.text(report_text)