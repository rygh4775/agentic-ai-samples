# Strands SDK Issue #1285 Reproduction & Workaround

Bedrock/Claude 모델이 MCP 도구의 중첩된 객체 매개변수를 JSON 문자열로 잘못 직렬화하는 문제를 재현하고 workaround를 제공합니다.

- GitHub Issue: https://github.com/strands-agents/sdk-python/issues/1285

## 파일 구조

- `ecs_agent.py` - 문제 재현 (ValidationError 발생)
- `workaround_ecs_agent.py` - Workaround 적용 (정상 동작)
- `requirements.txt` - 필요한 의존성

## 설치 및 실행

```bash
pip install -r requirements.txt
aws configure

# 문제 재현
python ecs_agent.py

# Workaround 적용
python workaround_ecs_agent.py
```

## 비교 분석 결과

### ecs_agent.py (문제 재현)
- **12번의 tool 호출 시도** 모두 실패
- 매번 동일한 `ValidationError` 발생:
  ```
  Input should be a valid dictionary [type=dict_type, 
  input_value='{"ecs_cluster_name": "my...", "time_window": 3600}', input_type=str]
  ```
- Claude 모델이 `parameters`를 **JSON 문자열**로 전달
- 실행 시간: ~60초 (재시도 반복)

### workaround_ecs_agent.py (해결)
- **1번의 tool 호출로 성공**
- `ValidationError` 없음
- 실행 시간: ~13초

### 비교표

| 항목 | ecs_agent.py | workaround_ecs_agent.py |
|------|-----------|---------------------|
| Tool 호출 횟수 | 12회 (모두 실패) | 1회 (성공) |
| ValidationError | 발생 | 없음 |
| parameters 타입 | JSON 문자열 | dict 객체 |

## Workaround 원리

`MCPClient.call_tool_async`를 monkey-patch하여 MCP 서버로 전달되기 전에 JSON 문자열을 dict로 변환:

```python
def fix_json_strings(args: dict) -> dict:
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

_original_call_tool_async = MCPClient.call_tool_async

async def patched_call_tool_async(self, tool_use_id, name, arguments=None, read_timeout_seconds=None):
    return await _original_call_tool_async(
        self, tool_use_id, name, fix_json_strings(arguments) if arguments else arguments, read_timeout_seconds
    )

MCPClient.call_tool_async = patched_call_tool_async
```

## 환경

- strands-agents: 1.19.0+
- Python: 3.10+
- MCP Server: awslabs.ecs-mcp-server
- Model: Bedrock Claude (us.anthropic.claude-sonnet-4-20250514-v1:0)
