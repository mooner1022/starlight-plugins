기기에서 HTTP 서버를 열고, 들어온 요청을 프로젝트 스크립트로 처리할 수 있어요.
웹훅 수신, 봇 상태 API, 간단한 웹 페이지 제공 등에 쓸 수 있어요.

## 사용법

프로젝트 설정에서 **웹 서버 설정** 이벤트를 허용하고 함수를 작성하세요. 프로젝트가 컴파일될 때마다 호출돼요.

```js
export function onWebServerSetup(server) {
    // 반환값이 응답이 돼요. 객체는 JSON, 문자열은 텍스트로 보내요.
    server.get("/hello/:name", (req) => ({ hello: req.params.name }));

    // res로 직접 응답하거나, async 함수로 비동기 처리도 할 수 있어요.
    server.post("/webhook", async (req, res) => {
        const data = JSON.parse(req.body);
        res.status(201).json({ received: true });
    });

    // 프로젝트 폴더의 public 디렉터리를 /files 아래로 제공해요.
    server.serveStatic("/files", "public");
}
```

NeonJS에서는 함수를 `export` 해야 해요. Rhino에서는 `export` 없이 쓰거나, 전역 `WebServer` 객체로 바로 등록할 수 있어요.

## 기능

- `:param`, `*` 경로 패턴과 GET/POST/PUT/PATCH/DELETE 등 모든 메서드
- `req.params`, `req.query`, `req.headers`, `req.body`, `req.form`
- `res.status()`, `res.json()`, `res.send()`, `res.html()`, `res.file()`, `res.redirect()`
- 접근 토큰 인증(Bearer 또는 `?token=`), CORS, 본문 크기·처리 시간 제한
- 서버 상태, 접속 주소, 요청 그래프와 최근 요청을 보여주는 홈 위젯

자세한 API는 [GitHub](https://github.com/mooner1022/starlight-webserver)를 참고하세요.
