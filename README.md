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

* Semantic Kernel Python과 MCP Integration 샘플임. 
  (Integrating Semantic Kernel Python with MCP)

### MCP 서버가동
```sh
cd mcp
cp ../.env ./
uv run mcp_server.py
```

### MCP 클라이언트 실행
```sh
uv run mcp_client.py
```

### 핵심코드

* 이 코드는 MCP 서버에서 제공하는 도구들을 동적으로 Semantic Kernel Function에 통합하는 기능을 구현한 것임.  
* `integrate_tools` 메서드는 MCP 서버에서 도구 목록을 가져와서 각 도구의 이름, 설명, 입력 스키마를 기반으로 동적으로 함수를 만듦.  
* 만들어진 함수는 `exec`를 써서 런타임에 정의되고, 각 도구의 호출 로직을 포함함. 이후, 만들어진 함수는 `kernel_function` 데코레이터를 통해 Semantic Kernel에 등록되고, 마지막으로 `self.kernel.add_functions`를 통해 `MCPPlugin`으로 추가됨.  
* 이 방식은 도구의 입력 스키마에 따라 유연하게 함수가 만들어지고 호출될 수 있도록 설계된 것임.

```python

async def integrate_tools(self) -> KernelPlugin:
        """Integrate tools into the kernel"""
        functions = {}
        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        for tool in available_tools:
            tool_name = tool["name"]
            tool_description = tool["description"]
            tool_input_schema = tool["input_schema"]

            # 인자 값 입력스키마에 따라 동적 함수 생성
            prop_names = list(tool_input_schema.get("properties", {}).keys())
            params_str = ", ".join(prop_names)  # e.g., "input" or "param1, param2"
            input_data_mapping = ", ".join([f"'{name}': {name}" for name in prop_names])
            func_code = (
                f"async def dynamic_tool_function({params_str}):\n"
                f"    input_data = {{{input_data_mapping}}}\n"
                f"    return await self.session.call_tool(tool_name, input_data)"
            )
            local_vars = {}
            exec(func_code, {"self": self, "tool_name": tool_name}, local_vars)
            dynamic_tool_function = local_vars["dynamic_tool_function"]

            tool_function = kernel_function(name=tool_name, description=tool_description)(dynamic_tool_function)
            functions[tool_name] = tool_function
        return self.kernel.add_functions(plugin_name="MCPPlugin", functions=functions)

```
* 전체 샘플은 [여기](./mcp)

## Reference

Forked from https://github.com/microsoft/semantic-kernel, then customized and localized for workshop.
