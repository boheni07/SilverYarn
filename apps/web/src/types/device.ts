/** design.md §3.1 Device — schema.md `devices` 테이블과 1:1 매핑. */
export type InstallMode = "kiosk" | "normal";

export interface Device {
  id: string;
  displayId: string;
  modelName?: string;
  userId: string;
  ramGb: number;
  androidVersion: string;
  installMode: InstallMode;
  slmModelVersion?: string;
  promptPackVersion?: string;
  installedAt: string;
}
