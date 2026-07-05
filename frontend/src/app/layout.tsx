import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { CommandCenterLayout } from "@/components/layout/CommandCenterLayout";
import { TooltipProvider } from "@/components/ui/tooltip";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SBI Vishwas | AI Command Center",
  description: "Enterprise Agentic AI Banking Operating System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="antialiased">
      <body className={inter.className}>
        <TooltipProvider>
          <CommandCenterLayout>{children}</CommandCenterLayout>
        </TooltipProvider>
      </body>
    </html>
  );
}
