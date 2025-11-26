# app.py

import os
import fitz # PyMuPDF
import streamlit as st
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool
from langchain.schema import AIMessage, HumanMessage

# --- 1. CONFIGURATION ---
# Use Streamlit secrets or sidebar input for API Key
if "GROQ_API_KEY" not in os.environ:
    st.sidebar.title("Configuration")
    api_key = st.sidebar.text_input("Enter your GROQ API Key", type="password")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    else:
        st.warning("Please enter your GROQ API Key to proceed.")
        st.stop()
        
        
        
# app.py continued

@st.cache_data
def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    if uploaded_file is None:
        return ""
    
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        text = "\n".join([page.get_text("text") for page in doc])
    return text


# app.py continued

@st.cache_resource
def setup_agent(pdf_text_input, groq_api_key):
    """Initializes the LangChain Agent with the necessary tools and memory."""
    if not groq_api_key:
        return None, None

    # Initialize Chat Model
    chat_model = ChatGroq(temperature=0, model_name="llama3-70b-8192", groq_api_key=groq_api_key)

    # Memory for Context Retention
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    memory.chat_memory.add_user_message("Start analyzing financial data")
    memory.chat_memory.add_ai_message("I am ready to analyze. Please provide the data.")

    # Define PDF Processing Tool
    def analyze_financial_report(query):
        """Analyzes financial data from a report."""
        if not pdf_text_input:
            return "Error: Financial report text is not available."

        # Use the query from the agent to make the analysis focused
        prompt = f"""
        You are a financial analyst. Analyze the following financial report text to answer this question: "{query}".

        Report Text (limited to 4000 chars):
        {pdf_text_input[:4000]}
        """
        response = chat_model.invoke(prompt)
        return response.content

    pdf_tool = Tool(
        name="Financial Report Analysis",
        func=analyze_financial_report,
        description="Analyzes financial data from reports to answer specific user questions. Use this tool *only* if the question relates to the financial report content."
    )

    # Initialize Agent
    agent = initialize_agent(
        agent="chat-conversational-react-description",
        tools=[pdf_tool],
        llm=chat_model,
        memory=memory,
        verbose=False # Set to False for cleaner UI output
    )
    return agent, memory



# app.py continued

# --- 4. STREAMLIT APP LAYOUT ---

st.title("🤖 LangChain Financial Analysis Agent")
st.markdown("Upload a PDF and chat with the AI Analyst about the financial data.")

# File Uploader
uploaded_file = st.file_uploader("Upload Financial Report PDF", type="pdf")

if uploaded_file:
    pdf_text = extract_text_from_pdf(uploaded_file)
    st.success(f"PDF uploaded and {len(pdf_text)} characters extracted.")
    
    # Initialize Agent
    agent, memory = setup_agent(pdf_text, os.environ.get("GROQ_API_KEY"))

    if agent:
        # Initialize chat history in session state
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Ask about the report (e.g., 'Summarize revenue trends')"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing report..."):
                    # Use invoke() instead of deprecated run()
                    response = agent.invoke({"input": prompt}) 
                    agent_response = response["output"]
                st.markdown(agent_response)
            
            st.session_state.messages.append({"role": "assistant", "content": agent_response})
    else:
        st.error("Agent could not be initialized. Check your GROQ API Key.")

# Optional: Add a text area to show the extracted text for debugging
with st.expander("View Extracted PDF Text"):
     st.text(pdf_text)