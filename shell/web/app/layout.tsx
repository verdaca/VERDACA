import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = {
  title: "Praxis — Strategic Analysis with Genuine Dissent",
  description:
    "Strategic analysis with genuine dissent. In minutes, not weeks.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className="bg-background text-foreground font-sans antialiased">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
