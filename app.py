import streamlit as st
import boto3
import json
import uuid

# --- CONFIG ---
AGENT_ARN = "arn:aws:bedrock-agentcore:ap-south-1:481048082409:runtime/langagent-FgVlZkDs5k"
ACCOUNT_ID = "481048082409"

st.set_page_config(page_title="Lauki FAQ Assistant", page_icon="🥒")

# 1. Initialize Session (Ensures 33+ character length)
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
            client = boto3.client("bedrock-agentcore", region_name="ap-south-1")
            
            # --- THE CRITICAL FIX ---
            # We wrap the prompt in the 2026 'input' schema and ENCODE to bytes
            request_body = json.dumps({"input": {"prompt": prompt}}).encode('utf-8')
            
            response = client.invoke_agent_runtime(
                agentRuntimeArn=AGENT_ARN,
                #accountId=ACCOUNT_ID,
                qualifier="DEFAULT",
                runtimeSessionId=st.session_state.session_id,
                payload=request_body,  # MUST be the encoded variable
                contentType="application/json",
                accept="application/json"
            )

            # 3. Handle Streaming Response
            full_text = ""
            placeholder = st.empty()
            
            for event in response.get('response'):
                if 'chunk' in event:
                    # Chunks are returned as bytes, must decode to string for UI
                    text_chunk = event['chunk']['bytes'].decode('utf-8')
                    full_text += text_chunk
                    placeholder.markdown(full_text + "▌")
            
            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

        except Exception as e:
            st.error(f"Error calling agent: {e}")
