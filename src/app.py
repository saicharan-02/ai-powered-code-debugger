import streamlit as st
import requests
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
import json
from pathlib import Path
import aiohttp
import asyncio

# Configure page settings
st.set_page_config(
    page_title="AI Code Debugger",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .output-container {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 20px;
        margin: 10px 0;
    }
    .error-message {
        color: #ff4b4b;
        padding: 10px;
        border-left: 3px solid #ff4b4b;
        background-color: #ffd7d7;
        margin: 5px 0;
    }
    .suggestion-message {
        color: #0068c9;
        padding: 10px;
        border-left: 3px solid #0068c9;
        background-color: #f0f7ff;
        margin: 5px 0;
    }
    .performance-tip {
        color: #09ab3b;
        padding: 10px;
        border-left: 3px solid #09ab3b;
        background-color: #e6f9ed;
        margin: 5px 0;
    }
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #1a67d2;
        color: white;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f0f2f6;
        color: #0e1117;
        margin-right: 20%;
        border: 1px solid #dfe1e6;
    }
    .chat-message strong {
        color: inherit;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Title and description
st.title("🔍 AI Code Debugger")
st.markdown("""
This tool helps you debug Python code using AI-powered analysis. It can:
- Detect syntax and logical errors
- Suggest performance improvements
- Provide interactive debugging assistance
""")

# Sidebar with options
with st.sidebar:
    st.header("⚙️ Settings")
    analysis_mode = st.selectbox(
        "Analysis Mode",
        ["Basic", "Detailed", "Performance Focus"]
    )
    
    st.markdown("---")
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. Paste your code or upload a file
    2. Click 'Analyze Code'
    3. Review the suggestions
    4. Use the chat for specific questions
    """)

# Main content area
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📝 Code Input")
    
    # Code input options
    input_method = st.radio("Input Method", ["Paste Code", "Upload File"])
    
    if input_method == "Paste Code":
        code = st.text_area("Enter your Python code here:", height=300)
    else:
        uploaded_file = st.file_uploader("Upload a Python file", type=["py"])
        if uploaded_file:
            code = uploaded_file.getvalue().decode("utf-8")
            st.code(code, language="python")

    if st.button("🔍 Analyze Code", type="primary"):
        if 'code' in locals() and code.strip():
            with st.spinner("Analyzing code..."):
                # Make API request to backend
                try:
                    response = requests.post(
                        "http://localhost:8000/analyze",
                        json={"code": code}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Store results in session state
                        st.session_state.analysis_result = result
                        
                        # Show success message
                        st.success("Analysis complete! Check the results panel.")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to the backend server: {str(e)}")
        else:
            st.warning("Please enter or upload some code first.")

with col2:
    st.subheader("🔍 Analysis Results")
    
    if 'analysis_result' in st.session_state:
        result = st.session_state.analysis_result
        
        # Display errors
        if result["errors"]:
            st.markdown("### ❌ Errors Found")
            for error in result["errors"]:
                with st.expander(f"Line {error['line']}: {error['type']}"):
                    st.markdown(f"""
                    **Message:** {error['message']}  
                    **Severity:** {error['severity']}
                    """)
        else:
            st.markdown("### ✅ No Errors Found")
        
        # Display suggestions
        if result["suggestions"]:
            st.markdown("### 💡 Suggestions")
            for suggestion in result["suggestions"]:
                with st.expander(f"Suggestion for line {suggestion['line']}"):
                    st.markdown(suggestion["suggestion"])
        
        # Display performance tips
        if result["performance_tips"]:
            st.markdown("### ⚡ Performance Tips")
            for tip in result["performance_tips"]:
                with st.expander(f"Optimization for line {tip['line']}"):
                    st.markdown(f"""
                    **Issue:** {tip['message']}  
                    **Suggestion:** {tip['suggestion']}
                    """)

# Chat interface
st.markdown("---")
st.subheader("💬 Debugging Assistant")

# Chat input
user_message = st.text_input("Ask a question about your code:")
if st.button("Send", key="chat_send"):
    if user_message:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        
        # Get code context
        code_context = code if 'code' in locals() else ""
        
        # Make API request to chat endpoint
        try:
            response = requests.post(
                "http://localhost:8000/chat",
                json={
                    "message": user_message,
                    "code_context": code_context
                }
            )
            
            if response.status_code == 200:
                assistant_response = response.json()["response"]
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
            else:
                st.error(f"Error: {response.text}")
        except Exception as e:
            st.error(f"Failed to get response: {str(e)}")

# Display chat history
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong><br>{message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>Assistant:</strong><br>{message["content"]}
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    st.markdown("---")
    st.markdown("Made with ❤️ by AI Code Debugger") 