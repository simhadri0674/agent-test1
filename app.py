import streamlit as st
import boto3
import json
import uuid

# --- CLOUD CONFIG ---
AGENT_ARN = "arn:aws:bedrock-agentcore:ap-south-1:481048082409:runtime/langagent-FgVlZkDs5k"
ACCOUNT_ID = "481048082409"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("🥒 Lauki FAQ Assistant")

if prompt := st.chat_input("Ask about Lauki..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            client = boto3.client("bedrock-agentcore", region_name="ap-south-1")
            
            # Use the EXACT structure the backend now expects
            payload_dict = {"input": {"prompt": prompt}}
            
            # MANDATORY: Convert to bytes for the 2026 SDK
            binary_payload = json.dumps(payload_dict).encode('utf-8')

            response = client.invoke_agent_runtime(
                agentRuntimeArn=AGENT_ARN,
                #accountId=ACCOUNT_ID,
                qualifier="DEFAULT",
                runtimeSessionId=st.session_state.session_id,
                payload=binary_payload, # This is the bytes object
                contentType="application/json",
                accept="application/json"
            )

            # Handle response stream
            full_text = ""
            placeholder = st.empty()
            for event in response.get('response'):
                if 'chunk' in event:
                    full_text += event['chunk']['bytes'].decode('utf-8')
                    placeholder.markdown(full_text + "▌")
            placeholder.markdown(full_text)

        except Exception as e:
            st.error(f"Cloud Execution Error: {e}")
