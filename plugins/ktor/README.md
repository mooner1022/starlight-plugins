다른 StarLight 플러그인이 함께 쓰는 [Ktor](https://ktor.io) 3.6.0 런타임(CIO 서버)이에요.
이 플러그인만으로는 아무 일도 하지 않고, 이 플러그인이 필요한 플러그인을 설치하면 함께 설치돼요.

## 포함된 것

- Ktor CIO 서버 3.6.0
- Ktor 로그를 StarLight 로그(`Ktor/…` 태그)로 보내는 SLF4J 연결

## 플러그인 개발자라면

Ktor를 플러그인에 직접 넣지 말고 이 플러그인에 의존하세요. 여러 플러그인이 Ktor를 하나만 불러와서 용량과 메모리를 아낄 수 있어요.

```json
"dependency": ["ktor@3.6.0"]
```

```groovy
compileOnly "io.ktor:ktor-server-cio:3.6.0"
```

자세한 내용은 [GitHub](https://github.com/mooner1022/starlight-ktor)를 참고하세요.
