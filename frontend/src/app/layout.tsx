import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LiveRefresher } from "@/components/live-refresher";
import { SidebarDupla } from "@/components/sidebar-dupla";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Relatórios · GS VoIP",
  description: "ASR, ACD e PDD por cliente, coletados do NextRouter SoftSwitch.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex h-full">
        <LiveRefresher />
        <SidebarDupla />
        <div className="min-w-0 flex-1 overflow-y-auto">{children}</div>
      </body>
    </html>
  );
}
