import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";

import { Header } from "@/components/Header";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Document Intelligence | AI Extraction Platform",
  description:
    "Upload PDFs and images, describe what to extract, and receive structured JSON from AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-slate-50 font-sans text-slate-900">
        <Header />
        <main className="flex-1">{children}</main>
        <Toaster
          position="top-right"
          richColors
          closeButton
          toastOptions={{
            className: "font-sans text-sm",
          }}
        />
      </body>
    </html>
  );
}
