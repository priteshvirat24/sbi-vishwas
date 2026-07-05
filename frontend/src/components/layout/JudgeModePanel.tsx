"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";

export function JudgeModePanel() {
  const router = useRouter();

  return (
    <motion.div 
      className="fixed bottom-6 right-6 z-50"
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 1, type: "spring", stiffness: 200, damping: 20 }}
    >
      <Button 
        onClick={() => router.push('/judge')}
        className="rounded-full shadow-2xl bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-6 flex items-center gap-2 border border-indigo-500/50 hover:scale-105 transition-transform"
      >
        <Play className="h-5 w-5 fill-current" />
        <span className="font-semibold tracking-wide uppercase text-sm">Run Cinematic Judge Mode</span>
      </Button>
    </motion.div>
  );
}
