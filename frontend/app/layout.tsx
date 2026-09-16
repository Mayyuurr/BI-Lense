import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BI-Lense | SME Decision Intelligence",
  description: "AI-Driven Decision Intelligence & Decision Support Platform for SMEs",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
