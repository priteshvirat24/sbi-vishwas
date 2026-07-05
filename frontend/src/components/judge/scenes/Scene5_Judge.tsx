import { motion } from "framer-motion";
import { Scale, CheckCircle2 } from "lucide-react";

export function Scene5_Judge({ progress }: { progress: number }) {
  // Score animates from 0 to 96
  const score = Math.min(Math.floor(progress * 150), 96);
  
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }} 
      animate={{ opacity: 1, scale: 1 }} 
      exit={{ opacity: 0, scale: 1.1 }}
      className="absolute inset-0 flex flex-col items-center justify-center p-12 pointer-events-none"
    >
      <div className="flex flex-col items-center">
        <div className="h-20 w-20 rounded-full bg-white/10 flex items-center justify-center mb-8 border border-white/20 shadow-[0_0_50px_rgba(255,255,255,0.1)]">
          <Scale className="h-10 w-10 text-white" />
        </div>
        
        <h2 className="text-3xl font-light tracking-widest uppercase mb-12 text-white/80">Judge Evaluation</h2>
        
        {/* Radial Progress Score */}
        <div className="relative w-64 h-64 flex items-center justify-center">
          <svg className="absolute inset-0 w-full h-full -rotate-90">
            <circle 
              cx="128" cy="128" r="120" 
              stroke="rgba(255,255,255,0.1)" strokeWidth="8" fill="none" 
            />
            <motion.circle 
              cx="128" cy="128" r="120" 
              stroke="#34d399" strokeWidth="8" fill="none" strokeLinecap="round"
              initial={{ strokeDasharray: "0 1000" }}
              animate={{ strokeDasharray: `${(score / 100) * 754} 1000` }}
            />
          </svg>
          <div className="flex flex-col items-center">
            <span className="text-6xl font-mono font-bold text-white">{score}</span>
            <span className="text-sm uppercase tracking-widest text-white/50 mt-1">/ 100</span>
          </div>
        </div>

        {/* Verdict */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: progress > 0.7 ? 1 : 0, y: progress > 0.7 ? 0 : 20 }}
          className="mt-12 flex items-center gap-3 px-8 py-4 rounded-full bg-emerald-500/20 border border-emerald-500/50 shadow-[0_0_40px_rgba(52,211,153,0.3)]"
        >
          <CheckCircle2 className="h-8 w-8 text-emerald-400" />
          <span className="text-2xl font-black tracking-widest text-emerald-400 uppercase">Resolution Approved</span>
        </motion.div>
      </div>
    </motion.div>
  );
}
