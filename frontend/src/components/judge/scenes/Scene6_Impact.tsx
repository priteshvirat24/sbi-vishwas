import { motion } from "framer-motion";
import { MessageSquare, ShieldCheck, Heart, Clock } from "lucide-react";

export function Scene6_Impact({ progress }: { progress: number }) {
  
  return (
    <motion.div 
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }} 
      exit={{ opacity: 0 }}
      className="absolute inset-0 flex flex-col pointer-events-none"
    >
      
      {/* Top Half: Customer SMS */}
      <div className="h-[40%] flex flex-col items-center justify-end pb-8">
        <motion.div 
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: progress > 0.1 ? 1 : 0 }}
          className="bg-[#2C2C2E] p-4 rounded-3xl max-w-sm border border-[#3A3A3C] shadow-2xl relative"
        >
          <div className="absolute -left-3 bottom-4 w-6 h-6 bg-[#2C2C2E] rounded-full" style={{ clipPath: "polygon(100% 0, 0 100%, 100% 100%)" }} />
          <div className="flex items-center gap-2 text-white/50 text-[10px] uppercase font-bold tracking-widest mb-2">
            <MessageSquare className="h-3 w-3" /> SBI Alert
          </div>
          <p className="text-white text-sm leading-relaxed">
            Dear Customer, your zero-balance account has been successfully opened. We apologize for the earlier inconvenience. <b>No insurance purchase is required.</b>
          </p>
        </motion.div>
      </div>

      {/* Bottom Half: Impact Dashboard */}
      <div className="flex-1 bg-gradient-to-t from-black via-black/90 to-transparent flex flex-col items-center justify-center p-12">
        <motion.div 
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: progress > 0.3 ? 1 : 0 }}
          className="grid grid-cols-4 gap-8 w-full max-w-6xl mb-16"
        >
          <div className="text-center">
            <ShieldCheck className="h-8 w-8 text-emerald-400 mx-auto mb-3" />
            <p className="text-4xl font-black text-white font-mono">100%</p>
            <p className="text-xs uppercase tracking-widest text-white/50 mt-2">Compliance Score</p>
          </div>
          <div className="text-center">
            <Heart className="h-8 w-8 text-rose-400 mx-auto mb-3" />
            <p className="text-4xl font-black text-white font-mono">+42</p>
            <p className="text-xs uppercase tracking-widest text-white/50 mt-2">Trust Gain</p>
          </div>
          <div className="text-center">
            <Clock className="h-8 w-8 text-blue-400 mx-auto mb-3" />
            <p className="text-4xl font-black text-white font-mono">3hr</p>
            <p className="text-xs uppercase tracking-widest text-white/50 mt-2">Wait Prevented</p>
          </div>
          <div className="text-center">
            <MessageSquare className="h-8 w-8 text-purple-400 mx-auto mb-3" />
            <p className="text-4xl font-black text-white font-mono">0</p>
            <p className="text-xs uppercase tracking-widest text-white/50 mt-2">Branch Revisits</p>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: progress > 0.6 ? 1 : 0, scale: progress > 0.6 ? 1 : 0.9 }}
          className="text-center"
        >
          <h1 className="text-5xl font-black tracking-tighter text-white mb-4">SBI VISHWAS</h1>
          <p className="text-xl text-indigo-300 font-light tracking-widest">
            AI that protects customers.
          </p>
        </motion.div>
      </div>

    </motion.div>
  );
}
