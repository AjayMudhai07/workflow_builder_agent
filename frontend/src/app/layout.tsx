import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Image from "next/image";
import Link from "next/link";
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
  title: "IRA Workflow Builder",
  description: "Transform CSV data into insights with AI-powered workflow automation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <header className="border-b bg-background sticky top-0 z-50">
          <div className="container mx-auto px-4 py-3 flex items-center">
            <Link href="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <Image
                src="/irame-logo.svg"
                alt="Irame Logo"
                width={136}
                height={80}
                priority
                className="h-10 w-auto"
              />
            </Link>
          </div>
        </header>
        <main className="min-h-[calc(100vh-57px)]">
          {children}
        </main>
      </body>
    </html>
  );
}
