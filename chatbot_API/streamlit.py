import streamlit as st
import requests

# Configuration
API_URL = "https://your-api-endpoint.com/chat"  # Replace with your actual API URL
CHECKPOINT_ID = "your_predefined_checkpoint_id"  # Replace with your checkpoint ID

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Set up the page
st.title("Chatbot with Predefined Checkpoint")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to ask?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Prepare API request
    payload = {
        "message": prompt,
        "checkpoint_id": CHECKPOINT_ID
    }
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Call the API
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Get the response content
            api_response = response.json()
            assistant_response = api_response.get("response", "No response received")
            
            # Simulate streaming response
            for chunk in assistant_response.split():
                full_response += chunk + " "
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            message_placeholder.markdown(error_msg)
            assistant_response = error_msg
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})