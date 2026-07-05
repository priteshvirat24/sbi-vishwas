"use client";

import { motion } from "framer-motion";
import { CheckCircle2, ChevronRight, Workflow } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export type GraphNode = {
  id: string;
  label: string;
  status: "pending" | "active" | "completed" | "skipped";
  agent?: string;
};

export function AgentExecutionGraph({ nodes }: { nodes: GraphNode[] }) {
  return (
    <div className="w-full overflow-x-auto py-6">
      <div className="flex min-w-max items-center px-4">
        {nodes.map((node, index) => (
          <div key={node.id} className="flex items-center">
            {/* Node */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className={`relative flex w-48 flex-col items-center gap-2 rounded-xl border p-4 shadow-sm transition-colors ${
                node.status === "active"
                  ? "border-primary bg-primary/5 shadow-md"
                  : node.status === "completed"
                  ? "border-emerald-200 bg-emerald-50"
                  : "border-border/50 bg-background opacity-70"
              }`}
            >
              {/* Status Indicator */}
              <div className="absolute -top-3 flex h-6 w-6 items-center justify-center rounded-full bg-background border shadow-sm">
                {node.status === "completed" ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : node.status === "active" ? (
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary"></span>
                  </span>
                ) : (
                  <Workflow className="h-3 w-3 text-muted-foreground" />
                )}
              </div>

              <span className="text-sm font-semibold text-center">{node.label}</span>
              {node.agent && (
                <Badge variant="secondary" className="text-[10px] font-normal px-1.5 py-0">
                  {node.agent}
                </Badge>
              )}
            </motion.div>

            {/* Edge */}
            {index < nodes.length - 1 && (
              <div className="flex w-12 items-center justify-center">
                <ChevronRight className={`h-5 w-5 ${
                  nodes[index].status === "completed" ? "text-emerald-400" : "text-muted-foreground/30"
                }`} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
