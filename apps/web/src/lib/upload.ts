/**
 * sync-contract.md §4 2단계 — 발급받은 Presigned URL로 파일을 MinIO에 직접 PUT한다.
 *
 * ⚠️ 이 요청은 우리 백엔드가 아니라 MinIO로 직접 나가므로 `lib/api/client`(server-only,
 * JSON 봉투·Bearer 토큰 전제)를 쓰지 않는다 — 브라우저에서 파일 바이트를 그대로 보낸다.
 * 그래서 이 파일은 `server-only`가 아니고 클라이언트 컴포넌트에서 직접 호출한다.
 */
export async function uploadFileToPresignedUrl(uploadUrl: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": file.type },
  });
  if (!response.ok) {
    throw new Error(`파일 업로드에 실패했습니다 (MinIO 응답 ${response.status}).`);
  }
}
