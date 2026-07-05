import { motion } from "framer-motion";
import { Brain, Shield, Database, Scale, UserCheck, MessageSquare } from "lucide-react";

export function Scene2_Awakening({ progress }: { progress: number }) {
  
  const nodes = [
    { id: 'supervisor', label: 'Supervisor', icon: Brain, x: 50, y: 50 },
    { id: 'memory', label: 'Memory Qdrant', icon: Database, x: 20, y: 30 },
    { id: 'policy', label: 'Policy Check', icon: Shield, x: 80, y: 30 },
    { id: 'advocate', label: 'Customer Advocate', icon: UserCheck, x: 20, y: 70 },
    { id: 'judge', label: 'Judge Agent', icon: Scale, x: 80, y: 70 },
    { id: 'notification', label: 'Notification', icon: MessageSquare, x: 50, y: 90 },
  ];

  const edges = [
    { source: 'memory', target: 'supervisor' },
    { source: 'supervisor', target: 'policy' },
    { source: 'policy', target: 'advocate' },
    { source: 'advocate', target: 'judge' },
    { source: 'judge', target: 'notification' },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }} 
      exit={{ opacity: 0 }}
      className="absolute inset-0 pointer-events-none"
    >
      <div className="absolute inset-y-0 right-0 w-1/2 flex items-center justify-center">
        <div className="relative w-full h-[600px] max-w-2xl">
          
          {/* Edges */}
          <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 0 }}>
            {edges.map((edge, i) => {
              const sourceNode = nodes.find(n => n.id === edge.source)!;
              const targetNode = nodes.find(n => n.id === edge.target)!;
              return (
                <motion.line
                  key={`edge-${i}`}
                  x1={`${sourceNode.x}%`}
                  y1={`${sourceNode.y}%`}
                  x2={`${targetNode.x}%`}
                  y2={`${targetNode.y}%`}
                  stroke="rgba(99, 102, 241, 0.3)"
                  strokeWidth="2"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: progress > (i * 0.15) ? 1 : 0 }}
                  transition={{ duration: 1 }}
                />
              );
            })}
          </svg>

          {/* Nodes */}
          {nodes.map((node, i) => {
            const Icon = node.icon;
            const isActive = progress > (i * 0.15);
            return (
              <motion.div
                key={node.id}
                className="absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center"
                style={{ left: `${node.x}%`, top: `${node.y}%`, zIndex: 10 }}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: isActive ? 1 : 0, opacity: isActive ? 1 : 0 }}
                transition={{ type: "spring", bounce: 0.4 }}
              >
                <div className={`h-16 w-16 rounded-2xl flex items-center justify-center border-2 shadow-2xl backdrop-blur-md transition-colors duration-500
                  ${isActive ? 'bg-indigo-600/20 border-indigo-500 text-indigo-400 shadow-[0_0_30px_rgba(99,102,241,0.5)]' : 'bg-black/50 border-white/10 text-white/50'}`}
                >
                  <Icon className="h-8 w-8" />
                </div>
                <div className="mt-3 bg-black/80 px-3 py-1 rounded-full border border-white/10 text-xs font-bold tracking-widest uppercase">
                  {node.label}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
