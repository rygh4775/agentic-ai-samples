#!/usr/bin/env python3
"""문제 재현: Bedrock/Claude가 중첩 객체를 JSON 문자열로 직렬화하는 이슈"""
from mcp.client.stdio import stdio_client, StdioServerParameters
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

def main():
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        temperature=0.3
    )
    
    mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["--from", "awslabs.ecs-mcp-server", "ecs-mcp-server"]
        )
    ))
    
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(model=bedrock_model, tools=tools)
        
        response = agent(
            "Use the ecs_troubleshooting_tool to fetch service events. "
            "Set the parameters with ecs_cluster_name 'my-cluster', "
            "ecs_service_name 'my-service', and time_window 3600."
        )
        print("Response:", response)

if __name__ == "__main__":
    main()
