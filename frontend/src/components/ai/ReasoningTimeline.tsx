"use client";

import { motion } from "framer-motion";
import { CheckCircle2, ChevronDown, ChevronRight, Clock, HelpCircle, AlertCircle, Wrench } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export type ReasoningStep = {
  id: string;
  timestamp: string;
  title: string;
  description?: string;
  type: "thought" | "action" | "observation" | "decision" | "tool_call";
  status: "pending" | "running" | "completed" | "error";
  metadata?: Record<string, any>;
};

export function ReasoningTimeline({ steps }: { steps: ReasoningStep[] }) {
  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <ReasoningNode key={step.id} step={step} isLast={index === steps.length - 1} />
      ))}
    </div>
  );
}

function ReasoningNode({ step, isLast }: { step: ReasoningStep; isLast: boolean }) {
  const [expanded, setExpanded] = useState(false);

  const getIcon = () => {
    switch (step.type) {
      case "thought": return <HelpCircle className="h-4 w-4 text-blue-500" />;
      case "tool_call": return <Wrench className="h-4 w-4 text-orange-500" />;
      case "decision": return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
      case "error": return <AlertCircle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="relative flex gap-4">
      {/* Line connecting nodes */}
      {!isLast && (
        <div className="absolute left-4 top-8 bottom-[-16px] w-0.5 bg-border/50" />
      )}

      {/* Node Icon */}
      <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-background shadow-sm">
        {getIcon()}
      </div>

      {/* Content */}
      <div className="flex-1 pb-4">
        <Card className={`border-border/50 shadow-sm transition-all ${expanded ? 'bg-secondary/10' : 'hover:bg-secondary/20'}`}>
          <div 
            className="flex cursor-pointer items-center justify-between p-3"
            onClick={() => setExpanded(!expanded)}
          >
            <div className="flex flex-col">
              <span className="text-sm font-medium">{step.title}</span>
              <span className="text-xs text-muted-foreground">{step.timestamp}</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-[10px] uppercase tracking-wider">
                {step.type}
              </Badge>
              {expanded ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
            </div>
          </div>
          
          {expanded && (step.description || step.metadata) && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <CardContent className="px-3 pb-3 pt-0 text-sm border-t border-border/50 mt-2 pt-2">
                {step.description && <p className="mb-2 text-muted-foreground">{step.description}</p>}
                
                {step.metadata && Object.keys(step.metadata).length > 0 && (
                  <div className="rounded-md bg-secondary/30 p-2 font-mono text-[11px] overflow-x-auto">
                    <pre>{JSON.stringify(step.metadata, null, 2)}</pre>
                  </div>
                )}
              </CardContent>
            </motion.div>
          )}
        </Card>
      </div>
    </div>
  );
}
