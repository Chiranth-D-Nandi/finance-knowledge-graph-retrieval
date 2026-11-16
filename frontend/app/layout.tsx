import "./globals.css";
import React from "react";

export const metadata = {
  title: "Financial Knowledge Graph & Temporal Retrieval Platform",
  description: "Entity-Resolved Temporal Knowledge Graph, Grounded Retrieval & Market Impact Analytics",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0a1628] text-slate-100 min-h-screen antialiased flex flex-col">
        {children}
      </body>
    </html>
  );
}
