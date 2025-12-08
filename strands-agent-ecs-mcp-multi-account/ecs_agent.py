import os
import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

app = BedrockAgentCoreApp()

# Account별 Role ARN 매핑
ACCOUNT_ROLES = {
    "hscho+container": "arn:aws:iam::258452927903:role/ECSFullAccessRole",
    "hscho+int": "arn:aws:iam::767397951228:role/ECSFullAccessRole",
}

def get_assumed_credentials(role_arn):
    sts = boto3.client("sts")
    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName="ecs-agent-session"
    )
    return response["Credentials"]

@app.entrypoint
def invoke(payload, context):
    prompt = payload.get("prompt", "List all ECS clusters")
    accounts = payload.get("accounts", list(ACCOUNT_ROLES.keys()))
    
    results = {}
    for account in accounts:
        role_arn = ACCOUNT_ROLES.get(account)
        if not role_arn:
            results[account] = f"Error: Unknown account {account}"
            continue
            
        try:
            creds = get_assumed_credentials(role_arn)
            
            mcp_client = MCPClient(lambda c=creds: stdio_client(
                StdioServerParameters(
                    command="uvx",
                    args=["--from", "awslabs-ecs-mcp-server", "ecs-mcp-server"],
                    env={
                        "AWS_ACCESS_KEY_ID": c["AccessKeyId"],
                        "AWS_SECRET_ACCESS_KEY": c["SecretAccessKey"],
                        "AWS_SESSION_TOKEN": c["SessionToken"],
                        "AWS_REGION": "ap-northeast-2"
                    }
                )
            ))
            with mcp_client:
                tools = mcp_client.list_tools_sync()
                agent = Agent(tools=tools)
                response = agent(prompt)
                results[account] = str(response)
        except Exception as e:
            results[account] = f"Error: {e}"
    
    return {"results": results}

if __name__ == "__main__":
    app.run()
