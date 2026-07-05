import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Judge Experience Mode | SBI Vishwas",
  description: "Cinematic AI Banking Operating System Presentation",
};

export default function JudgeLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // This layout intentionally omits the CommandCenterLayout 
  // to provide a full-screen, cinematic canvas.
  return (
    <div className="min-h-screen bg-zinc-950 text-white overflow-hidden selection:bg-indigo-500/30">
      {children}
    </div>
  );
}
