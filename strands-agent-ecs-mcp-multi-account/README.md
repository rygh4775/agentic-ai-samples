# ECS Multi-Account Agent

Strands Agent를 사용하여 여러 AWS 계정의 ECS 클러스터 상태를 조회하는 에이전트입니다. AWS ECS MCP Server를 활용하며, Amazon Bedrock AgentCore Runtime에 배포됩니다.

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    AgentCore Runtime                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     ecs_agent.py                          │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │  │
│  │  │   Strands   │───▶│  ECS MCP    │───▶│   AWS ECS   │    │  │
│  │  │   Agent     │    │  Server     │    │   API       │    │  │
│  │  └─────────────┘    └─────────────┘    └─────────────┘    │  │
│  │         │                                     │           │  │
│  │         ▼                                     ▼           │  │
│  │  ┌─────────────┐                      ┌─────────────┐     │  │
│  │  │   boto3     │──── AssumeRole ────▶│ Cross-Acct  │      │  │
│  │  │   STS       │                      │ IAM Roles   │     │  │
│  │  └─────────────┘                      └─────────────┘     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Account A│   │ Account B│   │ Account N│
        │   ECS    │   │   ECS    │   │   ECS    │
        └──────────┘   └──────────┘   └──────────┘
```

## 파일 구조

```
sample-agents/
├── ecs_agent.py          # AgentCore 호환 에이전트 코드
├── requirements.txt      # Python 의존성
├── Dockerfile           # 컨테이너 빌드용
└── README.md
```

## 사전 요구사항

1. **AgentCore CLI 설치**
   ```bash
   uv tool install bedrock-agentcore-starter-toolkit
   ```

2. **Cross-Account IAM Role 설정**
   
   각 대상 계정에 ECS 읽기 권한이 있는 Role 생성:
   (참고용 예시)
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ecs:ListClusters",
           "ecs:DescribeClusters",
           "ecs:ListServices",
           "ecs:DescribeServices"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

3. **AgentCore Execution Role에 AssumeRole 권한 추가**
  (참고용 예시)
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "sts:AssumeRole",
         "Resource": [
           "arn:aws:iam::ACCOUNT_A:role/ECSReadOnlyRole",
           "arn:aws:iam::ACCOUNT_B:role/ECSReadOnlyRole"
         ]
       }
     ]
   }
   ```

## 설정

`ecs_agent.py`에서 계정과 Role ARN 매핑 수정:
(참고용 예시)
```python
ACCOUNT_ROLES = {
    "hscho+container": "arn:aws:iam::258452927903:role/ECSFullAccessRole",
    "hscho+int": "arn:aws:iam::767397951228:role/ECSFullAccessRole",
}
```

## 배포

```bash

# 1. 설정
agentcore configure --entrypoint ecs_agent.py --deployment-type container --non-interactive

# 2. 배포
agentcore launch --auto-update-on-conflict

# 3. 상태 확인
agentcore status
```

## 사용법

```bash
# 모든 계정의 ECS 클러스터 조회
agentcore invoke '{"prompt": "List all ECS clusters"}'

# 특정 계정만 조회
agentcore invoke '{"prompt": "List all ECS clusters", "accounts": ["hscho+container"]}'

# 클러스터 상세 정보 조회
agentcore invoke '{"prompt": "Describe the ECS cluster named my-cluster"}'
```

## 로그 확인

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/ecs_agent-xQg5wk31km-DEFAULT \
  --log-stream-name-prefix "2025/12/07/[runtime-logs]" \
  --follow --region us-west-2
```

## 정리

```bash
agentcore destroy --force
```
