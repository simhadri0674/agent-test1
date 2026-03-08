import streamlit as st
import boto3
import json
import uuid
import botocore

# --- VERSION CHECK ---
BOTO3_VERSION = boto3.__version__
# Bedrock AgentCore 2026 requires at least 1.40.0
IS_COMPATIBLE = botocore.__version__ >= "1.42.0"

# --- CONFIG ---
AGENT_ARN = "arn:aws:bedrock-agentcore:ap-south-1:481048082409:runtime/langagent-FgVlZkDs5k"
ACCOUNT_ID = "481048082409"

st.set_page_config(page_title="Lauki FAQ Assistant", page_icon="🥒")

if not IS_COMPATIBLE:
    st.error(f"❌ Cloud environment error: Boto3 version {BOTO3_VERSION} is too old. Update your requirements.txt to boto3>=1.42.0")
    st.stop()

# 1. Initialize Session
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🥒 Lauki FAQ Assistant")

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 2. Chat Input
if prompt := st.chat_input("Ask me about Lauki..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # In Cloud, verify your IAM Role has bedrock-agentcore:InvokeAgentRuntime permissions
            client = boto3.client("bedrock-agentcore", region_name="ap-south-1")
            
            # THE PAYLOAD: String -> JSON -> Bytes
            body = {"input": {"prompt": prompt}}
            binary_payload = json.dumps(body).encode('utf-8')
            
            response = client.invoke_agent_runtime(
                agentRuntimeArn=AGENT_ARN,
                #accountId=ACCOUNT_ID,
                qualifier="DEFAULT",
                runtimeSessionId=st.session_state.session_id,
                payload=binary_payload,
                contentType="application/json",
                accept="application/json"
            )

            # 3. Handle Streaming
            full_text = ""
            placeholder = st.empty()
            
            for event in response.get('response'):
                if 'chunk' in event:
                    text_chunk = event['chunk']['bytes'].decode('utf-8')
                    full_text += text_chunk
                    placeholder.markdown(full_text + "▌")
            
            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

        except Exception as e:
            st.error(f"Cloud Execution Error: {e}")
