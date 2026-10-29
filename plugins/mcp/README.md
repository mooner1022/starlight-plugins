기기에서 [MCP(Model Context Protocol)](https://modelcontextprotocol.io) 서버를 열어,
Claude Code 같은 AI 클라이언트가 StarLight 프로젝트를 읽고, 고치고, 컴파일하고, 디버그룸에서 직접 말을 걸어 볼 수 있게 해요.
프로젝트 스크립트가 AI용 도구를 직접 만들 수도 있어요.

**Ktor**, **Workspace** 플러그인이 함께 설치돼요. 같은 Workspace를 쓰는 웹 IDE와 변경 사항을 공유해요.

## 연결하기

1. 플러그인 설정 > 보안에서 **접근 토큰**을 정해요. 토큰이 없으면 모든 요청을 거부해요.
2. 제어 > 상태를 눌러 주소를 복사해요.
3. PC에서 클라이언트에 등록해요.

```sh
claude mcp add --transport http starlight http://192.168.0.2:8765/mcp \
  --header "Authorization: Bearer <토큰>"
```

## 내장 도구

- 프로젝트·파일 목록, 파일 읽기/쓰기/부분 수정/이름 바꾸기/삭제, 검색
- 컴파일하고 결과 로그 보기, 프로젝트 켜기/끄기
- 프로젝트 로그, 앱 로그 보기
- 디버그룸에서 메시지를 보내고 봇의 답장 받기
- 이벤트 켜고 끄기, 새 프로젝트 만들기
- 리소스(`@`로 파일 첨부)와 프롬프트(`/mcp__starlight__debug_project`)

설정에서 내장 도구를 끄거나 읽기 전용으로 바꿀 수 있어요.

## 스크립트에서 도구 만들기

프로젝트 설정에서 **MCP 도구 설정** 이벤트를 허용하고 함수를 작성하세요. 프로젝트가 컴파일될 때마다 호출돼요.

```js
export function onMcpSetup(server) {
    server.tool("weather", {
        description: "도시의 날씨를 알려 줘요",
        inputSchema: { city: "string", days: "integer?" },
    }, async (args) => {
        const r = await fetch(`https://example.com/weather?city=${args.city}`);
        return await r.json();
    });
}
```

NeonJS에서는 함수를 `export` 해야 해요. Rhino에서는 `export` 없이 쓰거나, 전역 `Mcp` 객체로 바로 등록할 수 있어요.

자세한 내용은 [GitHub](https://github.com/mooner1022/starlight-mcp)를 참고하세요.
