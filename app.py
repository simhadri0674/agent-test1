import streamlit as st
import boto3
import json
import uuid

# --- CONFIG ---
# Ensure the ARN is the FULL resource name
AGENT_ARN = "arn:aws:bedrock-agentcore:ap-south-1:481048082409:runtime/langagent-FgVlZkDs5k"
ACCOUNT_ID = "481048082409"

st.set_page_config(page_title="Lauki Assistant", page_icon="🥒")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("🥒 Lauki FAQ Assistant")

if prompt := st.chat_input("Ask about Lauki..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            client = boto3.client("bedrock-agentcore", region_name="ap-south-1")
            
            # --- THE PAYLOAD ---
            # Construct the exact dictionary your agent handler expects
            input_body = {"prompt": prompt} 
            
            # Encode it directly inside the call variable to be safe
            raw_payload = json.dumps(input_body).encode('utf-8')

            response = client.invoke_agent_runtime(
                agentRuntimeArn=AGENT_ARN,
                #accountId=ACCOUNT_ID,
                qualifier="DEFAULT",
                runtimeSessionId=st.session_state.session_id,
                payload=raw_payload, # THIS MUST BE BYTES
                contentType="application/json",
                accept="application/json"
            )

            # --- THE STREAM ---
            full_text = ""
            placeholder = st.empty()
            
            # response['response'] is an EventStream
            for event in response.get('response'):
                if 'chunk' in event:
                    # Bytes must be decoded back to string for Streamlit
                    chunk_text = event['chunk']['bytes'].decode('utf-8')
                    full_text += chunk_text
                    placeholder.markdown(full_text + "▌")
            
            placeholder.markdown(full_text)

        except Exception as e:
            st.error(f"Cloud Error: {str(e)}")
