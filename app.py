import streamlit as st
import boto3
import json
import uuid

# --- AWS CONFIGURATION ---
# Based on your previous logs: ap-south-1 (Mumbai)
AGENT_ARN = "arn:aws:bedrock-agentcore:ap-south-1:481048082409:runtime/langagent-FgVlZkDs5k"
ACCOUNT_ID = "481048082409"

st.set_page_config(page_title="Lauki FAQ Assistant", page_icon="🥒")

# 1. Initialize Session (AgentCore uses session_id for memory/traces)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🥒 Lauki FAQ Assistant")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 2. User Input
if prompt := st.chat_input("Ask me anything about Lauki..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Initialize the specific AgentCore runtime client
            client = boto3.client("bedrock-agentcore", region_name="ap-south-1")
            
            # THE CRITICAL FIX: Encode your JSON prompt into BYTES
            # Your backend handles: payload.get("input", {}).get("prompt")
            payload_data = {"input": {"prompt": prompt}}
            binary_payload = json.dumps(payload_data).encode('utf-8')

            response = client.invoke_agent_runtime(
                agentRuntimeArn=AGENT_ARN,
                #accountId=ACCOUNT_ID,
                qualifier="DEFAULT",
                runtimeSessionId=st.session_state.session_id,
                payload=binary_payload,  # Sending Bytes
                contentType="application/json",
                accept="application/json"
            )

            # 3. Handle Binary Streaming Response
            full_text = ""
            placeholder = st.empty()
            
            # AgentCore 2026 returns a 'response' EventStream
            for event in response.get('response'):
                if 'chunk' in event:
                    # Chunks are binary, decode to UTF-8 for the UI
                    text_chunk = event['chunk']['bytes'].decode('utf-8')
                    full_text += text_chunk
                    placeholder.markdown(full_text + "▌")
            
            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

        except Exception as e:
            st.error(f"Error connecting to Lauki Agent: {e}")
            # Diagnostic for Cloud deployment:
            st.info(f"Boto3 Version: {boto3.__version__}")
