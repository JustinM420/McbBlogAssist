# Import necessary libraries
import openai
import streamlit as st

# Set your OpenAI Assistant ID here
assistant_id = st.secrets["assistant_id"]

# Initialize the OpenAI client 
client = openai

# Initialize session state variables for file IDs and chat control
if "file_id_list" not in st.session_state:
    st.session_state.file_id_list = []

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "file_id_list" not in st.session_state:
    st.session_state.file_id_list = [
        "file-Itehq6tttAolL8TprlTSdKPi",
    ]

# Set up the Streamlit page with a title and icon
st.set_page_config(page_title="MCB Blog Assistant", page_icon=":cookie:", layout="wide")
st.header(":cookie: MCB Blog Assistant")

#Get the OPENAI API Key
openai.api_key = st.secrets["openai_api_key"]

# Button to start the chat session
if st.sidebar.button("Start New Chat"):
    st.session_state.start_chat = True
    # Create a thread once and store its ID in session state
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.write("thread id: ", thread.id)

# Define the function to process messages with citations
def process_message_with_citations(message):
    message_content = message.content[0].text.value
    return message_content

# Only show the chat interface if the chat has been started
if st.session_state.start_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Create a placeholder for status updates above the chat input
    status_placeholder = st.empty()

    # Display existing messages in the chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.code(message["content"], language="markdown")  # Change this if you don't want to display in code block
            else:
                st.markdown(message["content"])

    # Chat input for the user
    if prompt := st.chat_input("What are we writing about today?"):
        # Add user message to the state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add the user's message to the existing thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt,
            file_ids=st.session_state.file_id_list
        )
        
        # Create a run with additional instructions
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            instructions="""ou specialize in writing SEO-optimized blog articles in markdown format, 
            only blogs should be in markdown all other messages should be regularly formatted. 
            Always refer to your files when writing a blog, you will have access to files that provide information about the brand, 
            including brand voice and basic details. Additionally, you can access files with specific topics, 
            using this information as context for crafting blog articles. you will focus on creating content that aligns with SEO best practices, 
            ensuring the articles are informative, engaging, and optimized for search engines. you will tailor your writing to match the brand's 
            voice and adhere to any specific guidelines provided in the files. you should ask for clarification if the provided information is 
            insufficient or unclear, and you should avoid making assumptions about the brand or the topic. The writing style should be professional, 
            informative, and engaging, with a focus on providing value to the reader."""
        )

        # Poll for the run to complete and retrieve the assistant's messages
        while run.status not in ["completed", "failed"]:
            # Update the status in place using the placeholder
            status_placeholder.write(f"Run status: {run.status}")
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )

        # Replace old status with a message or clear it after completion/failed
        status_placeholder.write(f"Run status: {run.status}")  # You can clear this if you want

        # Retrieve messages added by the assistant
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Process and display assistant messages
        assistant_messages_for_run = [
            message for message in messages 
            if message.run_id == run.id and message.role == "assistant"
        ]
        for message in assistant_messages_for_run:
            full_response = process_message_with_citations(message)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            # Display assistant messages using st.code to include copy button
            with st.chat_message("assistant"):
                st.code(full_response, language="markdown")