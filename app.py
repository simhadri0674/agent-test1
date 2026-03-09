import streamlit as st
import boto3
import json
import uuid

# --- CONFIGURATION ---
# Your specific AgentCore Runtime ARN
AGENT_RUNTIME_ARN = "arn:aws:bedrock-agentcore:ap-south-1:481048082409:runtime/HRAgent-za7ytMAMfI"
REGION = "ap-south-1"

st.set_page_config(page_title="Tachyon HR Assistant", page_icon="🏢")
st.title("🏢 Tachyon HR Assistant")

# --- AWS CLIENT SETUP ---
# Ensure your local machine has AWS credentials configured (aws configure)
client = boto3.client("bedrock-agentcore", region_name="ap-south-1")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
# Bedrock AgentCore requires a unique session ID (min 33 chars)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4()) + "-" + str(uuid.uuid4())

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("Ask about leave policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Querying Tachyon HR Cloud..."):
            try:
                # Prepare the payload for your @app.entrypoint
                payload_json = json.dumps({"prompt": prompt})
                # 1. Invoke the AgentCore Runtime
                # Note: Ensure you are using the 'bedrock-agentcore' client
                aws_response = client.invoke_agent_runtime(
                    agentRuntimeArn=AGENT_RUNTIME_ARN,
                    runtimeSessionId=st.session_state.session_id,
                    payload=json.dumps({"prompt": prompt}), # What we SEND
                    contentType="application/json",
                    accept="application/json"
                )

                # 2. Extract the result from the 'response' key (NOT 'payload')
                # The 'response' key contains a StreamingBody object
                response_stream = aws_response["response"] 
                response_body = response_stream.read().decode("utf-8")
                data = json.loads(response_body)

                # 3. Extract your agent's text
                # This depends on what your @app.entrypoint in app.py returns
                # If you used: return {"response": ai_response}, then use data.get("response")
                full_response = data.get("response") or data.get("result") or "No response from agent."

                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                                
            except Exception as e:
                st.error(f"AWS Error: {str(e)}")

# --- SIDEBAR INFO ---
with st.sidebar:
    st.header("About")
    st.info("This agent uses Amazon Bedrock AgentCore and LangGraph to answer HR queries based on official PDF documentation.")
