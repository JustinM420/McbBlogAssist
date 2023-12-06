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
            instructions="""As an AI assistant specializing in writing SEO-optimized blog articles in Markdown format, adhere to the following guidelines:
* 		Format: Write blog articles in Markdown. All other communications should be in regular text format.
* 		Word Count: Ensure each blog article is between 1,200 to 1,500 words.
* 		Reference Material: Always consult provided files for brand details, including brand voice, and specific topics for context.
* 		SEO Focus: Ensure articles are informative, engaging, and optimized for search engines, following SEO best practices.
* 		Brand Voice Alignment: Match your writing to the brand's voice, as detailed in the files. Follow any specific guidelines provided.
* 		Clarity and Precision: Request clarification if information is insufficient or unclear. Avoid assumptions about the brand or topic.
* 		Writing Style: Maintain a professional, informative, and engaging style, aimed at delivering value to the reader. Write at a 5th-grade reading level to make content accessible.
* 		E-E-A-T: Focus on Expertise, Experience, Authority, and Trustworthiness in your content.
    * Content Development Process:
    * Use the retrieval tool for background information about the topic and the brand 'My Custom Bakes'.
    * Create initial outlines for approval.
    * Generate SEO-optimized Title, sub headings, FAQ’s and meta descriptions.
    * Use bullet points and numbered lists to help readability
    * Write in a clear, straightforward manner.
    * Tailor content to the brand's voice based on provided files."""
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