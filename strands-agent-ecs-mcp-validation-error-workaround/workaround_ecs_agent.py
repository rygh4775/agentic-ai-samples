#!/usr/bin/env python3
import json
from mcp.client.stdio import stdio_client, StdioServerParameters
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

def fix_json_strings(args: dict) -> dict:
    """JSON 문자열을 dict/list로 자동 변환"""
    if not args:
        return args
    fixed = {}
    for k, v in args.items():
        if isinstance(v, str) and v.startswith(('{', '[')):
            try:
                fixed[k] = json.loads(v)
            except json.JSONDecodeError:
                fixed[k] = v
        else:
            fixed[k] = v
    return fixed

# MCPClient의 call_tool_async를 패치
_original_call_tool_async = MCPClient.call_tool_async

async def patched_call_tool_async(self, tool_use_id, name, arguments=None, read_timeout_seconds=None):
    return await _original_call_tool_async(
        self, tool_use_id, name, fix_json_strings(arguments) if arguments else arguments, read_timeout_seconds
    )

MCPClient.call_tool_async = patched_call_tool_async

def main():
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        temperature=0.3
    )
    
    # 공식 Amazon ECS MCP Server 사용
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
