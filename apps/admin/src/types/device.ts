/** design.md §3.1(v0.7) Device — schema.md `devices` 테이블과 1:1 매핑.
 * apps/web/src/types/device.ts와 동일 — 공유 패키지가 아직 없어 두 앱이 각자 들고 있다. */
export type InstallMode = "kiosk" | "normal";

export interface Device {
  id: string;
  displayId: string;
  modelName?: string;
  userId: string;
  ramGb: number;
  androidVersion: string;
  installMode: InstallMode;
  aiTops?: number;
  slmModelVersion?: string;
  promptPackVersion?: string;
  installedAt: string;
  lastSyncAt?: string;
}

/** 한글 표시명 — schema.md §7에는 아직 install_mode 매핑이 없어(devices/sync_status
 * 계열 표는 §7에 없음) apps/admin 스캐폴딩 시 새로 정한 값. 나중에 §7에 정식 편입 필요. */
export const INSTALL_MODE_LABEL: Record<InstallMode, string> = {
  kiosk: "키오스크",
  normal: "일반",
};
