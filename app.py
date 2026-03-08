import streamlit as st
import boto3
import json
import uuid

# --- CONFIG ---
# Ensure these are exactly correct for your Mumbai deployment
AGENT_ARN = "arn:aws:bedrock-agentcore:ap-south-1:481048082409:runtime/langagent-FgVlZkDs5k"
ACCOUNT_ID = "481048082409"

st.set_page_config(page_title="Lauki Assistant", page_icon="🥒")

# Ensure session_id is persistent
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("🥒 Lauki FAQ Assistant")

if prompt := st.chat_input("Ask about Lauki..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Initialize client for ap-south-1
            client = boto3.client("bedrock-agentcore", region_name="ap-south-1")
            
            # 1. Create the dictionary
            # Note: For AgentCore, ensure this matches your handler's expected key
            input_body = {"input": {"prompt": prompt}}
            
            # 2. Convert to JSON String then to BYTES
            # This satisfies the 'payload (bytes)' requirement in Boto3 1.40+
            payload_bytes = json.dumps(input_body).encode('utf-8')

            response = client.invoke_agent_runtime(
                agentRuntimeArn=AGENT_ARN,
                #accountId=ACCOUNT_ID,
                qualifier="DEFAULT",
                runtimeSessionId=st.session_state.session_id,
                payload=payload_bytes,
                contentType="application/json",
                accept="application/json"
            )

            # 3. Handle the response stream
            full_text = ""
            placeholder = st.empty()
            
            for event in response.get('response'):
                if 'chunk' in event:
                    # Chunks are returned as bytes, must be decoded back to string
                    chunk_text = event['chunk']['bytes'].decode('utf-8')
                    full_text += chunk_text
                    placeholder.markdown(full_text + "▌")
            
            placeholder.markdown(full_text)

        except Exception as e:
            st.error(f"Cloud Error: {str(e)}")
            # Diagnostic for Cloud deployment:
            st.info(f"Boto3 Version: {boto3.__version__}")
