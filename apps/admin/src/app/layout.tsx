import type { Metadata } from "next";
import { Noto_Serif_KR } from "next/font/google";
import "./globals.css";

// apps/web과 동일한 서체 구성 — 관리자 화면은 --font-editorial을 거의 쓰지 않지만
// 디자인 토큰 변수 이름을 통일해 두 앱이 같은 @theme 블록을 유지하게 했다.
const notoSerifKr = Noto_Serif_KR({
  variable: "--font-noto-serif-kr",
  weight: ["400", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "은빛실타래 관리자",
  description: "은빛실타래 운영 관리 콘솔",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={notoSerifKr.variable}>
      <body className="min-h-screen font-ui text-body-compact text-ink">{children}</body>
    </html>
  );
}
