import streamlit as st
import boto3
import json

# Replace with your actual ARN from the deployment step
AGENT_ARN = "arn:aws:bedrock-agentcore:ap-south-1:481048082409:runtime/langagent-FgVlZkDs5k"

st.set_page_config(page_title="Lauki FAQ Assistant", page_icon="🥒")
st.title("🥒 Lauki FAQ Assistant")

# Initialize Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask me anything about Lauki..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call AWS Bedrock AgentCore
    with st.chat_message("assistant"):
        try:
            client = boto3.client("bedrock-agentcore", region_name="ap-south-1")
            
            # AgentCore 2026 Payload structure
            response = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_ARN.split('/')[-1],
            qualifier="DEFAULT",
            runtimeSessionId="streamlit-session-001",
            payload=json.dumps({"input": {"prompt": prompt}}).encode('utf-8'),
            contentType="application/json",
            accept="application/json"
            )
            
            # Handle streaming response
            #full_response = ""
            full_text = ""
            for event in response.get('response'):
                if 'chunk' in event:
                    full_text += event['chunk']['bytes'].decode('utf-8')
            
            st.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})
            
        except Exception as e:
            st.error(f"Error calling agent: {e}")
