import { motion } from "framer-motion";
import { User, AlertCircle, Clock, MapPin } from "lucide-react";

export function Scene1_Problem({ progress }: { progress: number }) {
  return (
    <motion.div 
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }} 
      exit={{ opacity: 0 }}
      className="absolute inset-0 flex items-center justify-start p-12 md:p-24"
    >
      <div className="w-full max-w-lg space-y-6">
        
        <motion.div 
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-secondary/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl shadow-2xl"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="h-12 w-12 rounded-full bg-white/10 flex items-center justify-center">
              <User className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Customer Visit</h3>
              <div className="flex items-center gap-2 text-white/50 text-xs">
                <MapPin className="h-3 w-3" /> Branch 401
                <Clock className="h-3 w-3 ml-2" /> Waiting 45 mins
              </div>
            </div>
          </div>
          
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: progress > 0.2 ? 1 : 0, scale: progress > 0.2 ? 1 : 0.9 }}
            className="bg-rose-500/10 border border-rose-500/30 p-4 rounded-xl relative"
          >
            <AlertCircle className="absolute -top-3 -right-3 h-6 w-6 text-rose-500 bg-black rounded-full" />
            <p className="text-sm italic text-rose-200">
              "They straight up told me it's mandatory to buy an insurance scheme from them to open a zero-balance savings account."
            </p>
          </motion.div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: progress > 0.6 ? 1 : 0, x: progress > 0.6 ? 0 : -50 }}
          className="bg-black/60 backdrop-blur-md border border-rose-500/50 p-4 rounded-xl flex items-center justify-between"
        >
          <span className="text-xs uppercase tracking-widest text-white/50">Frustration Meter</span>
          <div className="h-2 flex-1 mx-4 bg-white/10 rounded-full overflow-hidden">
            <motion.div 
              className="h-full bg-gradient-to-r from-orange-500 to-rose-500"
              initial={{ width: "20%" }}
              animate={{ width: "95%" }}
              transition={{ duration: 3, ease: "easeOut" }}
            />
          </div>
          <span className="text-rose-500 font-bold font-mono">CRITICAL</span>
        </motion.div>

      </div>
    </motion.div>
  );
}
