import type { Metadata } from "next";
import { Noto_Serif_KR } from "next/font/google";
import { AppHeader } from "@/components/AppHeader";
import "./globals.css";

// Pretendard(UI 서체)는 Google Fonts에 없어 npm 패키지로 자체 호스팅한다(globals.css에서
// import) — design-tokens.md 원문의 Google Fonts 링크 예시는 Pretendard 부분이 실제로는
// 존재하지 않는 URL이라 이 스캐폴딩에서 정정했다.
const notoSerifKr = Noto_Serif_KR({
  variable: "--font-noto-serif-kr",
  weight: ["400", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "은빛실타래",
  description: "어르신 자서전 제작 및 AI 말벗돌봄 플랫폼",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={notoSerifKr.variable}>
      <body className="min-h-screen">
        <AppHeader />
        {children}
      </body>
    </html>
  );
}
