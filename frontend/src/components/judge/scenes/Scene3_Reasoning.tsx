import { motion } from "framer-motion";
import { Terminal } from "lucide-react";

export function Scene3_Reasoning({ progress }: { progress: number }) {
  const steps = [
    { time: 0.1, text: "Policy conflict detected." },
    { time: 0.25, text: "Searching RBI knowledge base..." },
    { time: 0.4, text: "Loading SBI internal policy guidelines." },
    { time: 0.55, text: "Comparing requirements against branch behavior." },
    { time: 0.7, text: "Customer rights violation identified." },
    { time: 0.85, text: "Preparing resolution matrix." },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }} 
      exit={{ opacity: 0 }}
      className="absolute inset-0 flex items-center justify-start p-12 md:p-24 pointer-events-none"
    >
      <div className="w-full max-w-xl">
        <div className="flex items-center gap-3 mb-8">
          <Terminal className="h-6 w-6 text-indigo-400" />
          <h2 className="text-xl font-mono text-indigo-400 tracking-widest uppercase">Live Reasoning</h2>
        </div>
        
        <div className="space-y-6 border-l-2 border-indigo-500/30 pl-6 relative">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ 
                opacity: progress >= step.time ? (progress > step.time + 0.3 ? 0.4 : 1) : 0, 
                x: progress >= step.time ? 0 : -20 
              }}
              className="relative"
            >
              <div className={`absolute -left-[31px] top-1.5 h-3 w-3 rounded-full ${progress >= step.time ? 'bg-indigo-400 shadow-[0_0_10px_rgba(129,140,248,0.8)]' : 'bg-indigo-900'}`} />
              <p className="text-2xl md:text-3xl font-light tracking-tight">
                {step.text}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
