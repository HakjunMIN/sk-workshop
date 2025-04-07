# Semantic Kernel Workshop

## 환경설정

```bash
cp .env.example .env
```

`.env` 파일을 아래와 같이 설정

[Azure Open AI Service 생성하기 참고](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=programming-language-studio) 

[Azure AI Agent 생성하기 참고](https://learn.microsoft.com/ko-kr/azure/ai-services/agents/quickstart?pivots=ai-foundry-portal)

```sh
GLOBAL_LLM_SERVICE="AzureOpenAI"
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="https://..."
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="..."
AZURE_OPENAI_TEXT_DEPLOYMENT_NAME="..."
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="..."
AZURE_OPENAI_API_VERSION="..."
# AI Agent 프로젝트 
AZURE_AI_AGENT_PROJECT_CONNECTION_STRING=""
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME=""
```

## 필요패키지 설치

```sh
pip install -r requirements.txt
```

## Semantic Kernel 기본

* 기본구동
* 함수호출
* 채팅이력 및 관리
* 플래너 사용
* 메모리 및 임베딩
* 그라운드니스 체크
* 단일 프롬프트의 여러 응답 구현
* 스트리밍 처리

## Semantic Kernel Agentic AI

1. SK 멀티 Agent
  *  함수호출 및 디버깅
2. Azure AI Agent
  * 코드 인터프리터, 파일검색, 함수호출, 멀티 Agent 구현

## Model Context Protocol (MCP)  with Semantic Kernel 

### MCP 서버가동
```sh
cd mcp
cp ../.env ./
FLASK_APP=mcp_server flask run
```

### MCP 클라이언트 실행
```sh
python mcp_client.py
```

### 핵심코드

* MCP서버에서 제공하는 툴을 Semantic Kernel Function에 등록하여 Invoke되도록 함.

```python
class MCPIntegration:

    functions = {}

    def __init__(self, kernel, mcp_client):
        self.kernel: Kernel = kernel
        self.mcp_client: MCPClient = mcp_client
    
    def integrate_tools(self) -> KernelPlugin:
        tools = self.mcp_client.list_tools()
        for tool in tools:
            tool_name = tool["name"]
            tool_description = tool["description"]

            @kernel_function(name=tool_name, description=tool_description)
            async def tool_function(input_text):
                return self.mcp_client.execute_tool(tool_name, input_text)
            
            self.functions[tool_name] = tool_function

        return self.kernel.add_functions(plugin_name="MCPPlugin", functions=self.functions)


```

- Full sample: [here](./mcp/)

## Reference

Forked from https://github.com/microsoft/semantic-kernel, then customized and localized for workshop.
