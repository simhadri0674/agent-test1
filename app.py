import streamlit as st
import boto3
import json
import uuid

# --- CONFIGURATION ---
# Ensure these values are correct for your ap-south-1 deployment
AGENT_ARN = "arn:aws:bedrock-agentcore:ap-south-1:481048082409:runtime/langagent-FgVlZkDs5k"
AWS_ACCOUNT_ID = "481048082409"
REGION = "ap-south-1"

st.set_page_config(page_title="Lauki FAQ Assistant", page_icon="🥒", layout="centered")

# --- 1. SESSION INITIALIZATION ---
# AgentCore 2026 requires a runtimeSessionId of at least 33 characters.
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4()) # 36 chars

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🥒 Lauki FAQ Assistant")
st.caption("Powered by AWS Bedrock AgentCore")

# --- 2. DISPLAY CHAT HISTORY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 3. USER INPUT & AGENT INVOCATION ---
if prompt := st.chat_input("Ask me anything about Lauki..."):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Initialize client
            client = boto3.client("bedrock-agentcore", region_name=REGION)
            
            # Prepare the payload strictly as bytes
            # AgentCore 2026 expects the "input" -> "prompt" wrapper
            body = {"input": {"prompt": prompt}}
            payload_json = json.dumps(body)
            payload_bytes = payload_json.encode('utf-8')

            # The API call
            # Note: accountId is optional if included in ARN, but good for validation
            response = client.invoke_agent_runtime(
                agentRuntimeArn=AGENT_ARN,
                #accountId=AWS_ACCOUNT_ID,
                qualifier="DEFAULT",
                runtimeSessionId=st.session_state.session_id,
                payload=payload_bytes,
                contentType="application/json",
                accept="application/json"
            )
            
            # --- 4. STREAMING RESPONSE PROCESSING ---
            full_text = ""
            placeholder = st.empty() # For typing effect
            
            # The 'response' key contains a StreamingBody/EventStream
            for event in response.get('response'):
                if 'chunk' in event:
                    # Chunks also arrive as bytes; decode them for Streamlit
                    chunk_bytes = event['chunk']['bytes']
                    decoded_chunk = chunk_bytes.decode('utf-8')
                    full_text += decoded_chunk
                    placeholder.markdown(full_text + "▌")
            
            # Finalize assistant message
            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})
            
        except Exception as e:
            st.error(f"Error calling agent: {str(e)}")
            # Helpful tip if bytes error still occurs:
            if "bytes-like object" in str(e):
                st.warning("SDK Validation Failed: Ensure your boto3 version is 1.40.0+")
