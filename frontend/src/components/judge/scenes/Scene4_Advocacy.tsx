import { motion } from "framer-motion";
import { UserCheck, ShieldX, ShieldCheck, Check } from "lucide-react";

export function Scene4_Advocacy({ progress }: { progress: number }) {
  return (
    <motion.div 
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }} 
      exit={{ opacity: 0 }}
      className="absolute inset-0 flex items-center justify-center p-12 pointer-events-none"
    >
      <div className="w-full max-w-5xl bg-black/80 backdrop-blur-2xl border border-white/10 rounded-3xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]">
        
        {/* Header */}
        <div className="bg-indigo-600/20 p-6 flex items-center gap-4 border-b border-indigo-500/20">
          <div className="h-12 w-12 rounded-full bg-indigo-500 flex items-center justify-center">
            <UserCheck className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Customer Advocate Activated</h2>
            <p className="text-indigo-200">Evaluating resolution for "Forced Bundling" violation.</p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-xs uppercase tracking-widest text-indigo-300">Confidence Score</p>
            <p className="text-3xl font-mono font-bold text-white">98%</p>
          </div>
        </div>

        {/* Content */}
        <div className="p-8 grid grid-cols-2 gap-8">
          
          {/* Left: Policy Comparison */}
          <div className="space-y-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-white/50 mb-4">Policy Comparison</h3>
            
            <motion.div 
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: progress > 0.1 ? 1 : 0 }}
              className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10"
            >
              <div className="flex items-center gap-2 text-rose-400 mb-2 font-bold">
                <ShieldX className="h-5 w-5" /> Branch Action
              </div>
              <p className="text-sm text-rose-200">Mandating life insurance policy purchase to open a basic savings account.</p>
            </motion.div>

            <motion.div 
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: progress > 0.3 ? 1 : 0 }}
              className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10"
            >
              <div className="flex items-center gap-2 text-emerald-400 mb-2 font-bold">
                <ShieldCheck className="h-5 w-5" /> RBI Master Circular
              </div>
              <p className="text-sm text-emerald-200">Banks must not insist on opening of any other product as a precondition for savings accounts.</p>
            </motion.div>
          </div>

          {/* Right: Recommended Action */}
          <div className="space-y-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-white/50 mb-4">Proposed Resolution</h3>
            
            <div className="space-y-3">
              {[
                { time: 0.5, text: "Immediately waive insurance requirement." },
                { time: 0.6, text: "Automatically provision BSBD account." },
                { time: 0.7, text: "Issue official apology via SMS/App." },
                { time: 0.8, text: "Flag Branch 401 for compliance training." }
              ].map((item, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: progress > item.time ? 1 : 0, y: progress > item.time ? 0 : 10 }}
                  className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10"
                >
                  <div className="h-6 w-6 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0">
                    <Check className="h-4 w-4 text-emerald-500" />
                  </div>
                  <span className="text-sm font-medium">{item.text}</span>
                </motion.div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </motion.div>
  );
}
