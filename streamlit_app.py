import streamlit as st
from openai import OpenAI
import boto3
import json
from base64 import b64decode
from langchain_openai import ChatOpenAI

# Show title and description.
st.title("💬 Chatbot with Octo")
st.write(
    "This is a simple app where you can generate images. "
    "It's in development so for now you need to enter the AWS credentials here for it to work."
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
aws_access_key_id = st.text_input("AWS_ACCESS_KEY_ID", type="password")
aws_secret_access_key = st.text_input("AWS_SECRET_ACCESS_KEY", type="password")
aws_session_token = st.text_input("AWS_SESSION_TOKEN", type="password")

if not (aws_access_key_id and aws_secret_access_key and aws_session_token):
    st.info("Please add the AWS credentials.", icon="🗝️")
else:
    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        payload = {
            "prompt": prompt,
        }

        # Generate a response using the OpenAI API.
        RUN_MESSAGE = False
        if RUN_MESSAGE:
            # Create an OpenAI client.
            client = OpenAI(api_key="") # Use ChatOpenAI
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )

            # Stream the response to the chat using `st.write_stream`, then store it in 
            # session state.
            with st.chat_message("assistant"):
                response = st.write_stream(stream)
        else:
            session = boto3.session.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
            sm_runtime = session.client("sagemaker-runtime", region_name="us-east-1")
            response = sm_runtime.invoke_endpoint(
                EndpointName="my-super-octoai-sdxl",
                ContentType="application/json", Body=json.dumps(payload))
            response_json = json.loads(response["Body"].read().decode())
            decoded_image = b64decode(response_json["images"][0]["image_b64"])
            with open('img.jpg','wb') as f:
                f.write(decoded_image)
            response = decoded_image
        st.session_state.messages.append({"role": "assistant", "content": response})
