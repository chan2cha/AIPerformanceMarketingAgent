import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Signal Desk · 광고 소재 분석",
  description: "우리 브랜드와 경쟁 브랜드의 광고 소재를 모아 AI로 분석하는 작업 공간",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
