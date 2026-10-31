프로젝트 스크립트에서 카카오톡 채팅방으로 사진·동영상·파일을 보낼 수 있어요.
메신저봇의 MediaSender 모듈을 StarLight에 맞게 다시 만들었어요.

## 사용법

플러그인을 켜면 모든 프로젝트에 `MediaSharer`가 생겨요. 플러그인을 켜기 전에 컴파일된 프로젝트는 다시 컴파일하세요.

```js
export async function onMessage(msg) {
    // 보내고 끝: 카카오톡이 파일을 읽으면 바로 홈 화면으로 나가요.
    if (msg.message === "!고양이")
        MediaSharer.send(msg, "https://example.com/cat.jpg", { leave: "home" });

    // 결과가 필요하면 기다려요.
    if (msg.message === "!사진들") {
        const r = await MediaSharer.send(msg.room, ["images/a.png", "images/b.png"], { fileName: "앨범" });
        if (!r.ok)
            msg.room.send("전송 실패: " + r.error);
    }
}
```

`send()`는 다운로드를 기다리지 않고 바로 돌아와서, 그동안 온 메시지도 계속 처리해요. 결과는 NeonJS에서는 `await`,
Rhino에서는 `.join()`으로 받을 수 있어요.

## 기능

- **보낼 파일**: URL, 경로(프로젝트 폴더 기준 상대 경로도), data URL, Base64, `byte[]`, `Uint8Array`·`ArrayBuffer`, `Bitmap`, 그리고 이들의 배열
- **보낼 방**: `msg`, `msg.room`, 채널 ID, 메시지를 받은 적 있는 방 이름
- **옵션**: `fileName`(보낼 이름), `timeout`(다운로드 제한 시간), `cache`(다시 내려받지 않기), `headers`(요청 헤더), `leave`(전송 후 나갈 곳)
- **빠른 복귀**: 채팅방이 열려 있는 동안에는 카카오톡이 알림을 보내지 않아요. 카카오톡이 파일을 읽은 직후 홈 화면이나 StarLight로 나가서 놓치는 메시지를 줄여요.
- **형식 판별**: 확장자가 없는 URL도 내용을 보고 사진·동영상·문서를 구분해요.
- **듀얼 메신저**: 방마다 어느 카카오톡으로 온 메시지인지 기억해서 그 카카오톡으로 보내요.
- **설정**: 카카오톡·권한 상태, 다운로드·캐시·체류 시간 설정, 알려진 채팅방 목록, 최근 전송 기록

## 필요한 것

- StarLight nightly(PluginCore 1.0.0 이상). NeonJS에서 쓰려면 플러그인 Api를 NeonJS에 노출하는 nightly 빌드가 필요해요.
- StarLight의 **다른 앱 위에 표시** 권한. 없으면 StarLight가 화면에 떠 있을 때만 보낼 수 있어요. 플러그인 설정에서 바로 열 수 있어요.
- 듀얼 메신저 쪽 카카오톡으로 선택창 없이 보내려면, StarLight가 `INTERACT_ACROSS_USERS` 권한을 선언한 빌드에서 이 권한을 부여해야 해요.
  권한이 없으면 어느 카카오톡으로 보낼지 묻는 선택창이 떠요.
  ```sh
  adb shell pm grant dev.mooner.starlight android.permission.INTERACT_ACROSS_USERS
  ```

자세한 사용법과 테스트 스크립트는 [소스 저장소](https://github.com/mooner1022/starlight-mediasharer)에 있어요.
