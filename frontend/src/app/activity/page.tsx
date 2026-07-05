import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity, Bot, Shield, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const MOCK_ACTIVITY = [
  {
    id: 1,
    agent: "Policy Compliance",
    action: "Audited Case CJ-8904",
    detail: "Identified RBI Circular violation regarding minimum balance deductions.",
    time: "Just now",
    icon: Shield,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
  },
  {
    id: 2,
    agent: "Journey Tracker",
    action: "Merged Channels",
    detail: "Linked incoming WhatsApp message to existing Web case CJ-8901.",
    time: "2m ago",
    icon: Bot,
    color: "text-indigo-500",
    bg: "bg-indigo-500/10",
  },
  {
    id: 3,
    agent: "Judge Agent",
    action: "Rejected Resolution",
    detail: "Proposed resolution involved forced branch visit. Rerouted to Escalation Advocate.",
    time: "5m ago",
    icon: AlertCircle,
    color: "text-rose-500",
    bg: "bg-rose-500/10",
  },
  {
    id: 4,
    agent: "Supervisor",
    action: "Workflow Complete",
    detail: "Dormancy Reactivation workflow successfully completed for CJ-8899.",
    time: "12m ago",
    icon: CheckCircle2,
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
  },
  {
    id: 5,
    agent: "Knowledge Base",
    action: "Semantic Search",
    detail: "Retrieved RBI guidelines for zero-balance insurance requirements (Confidence: 98%).",
    time: "15m ago",
    icon: FileText,
    color: "text-amber-500",
    bg: "bg-amber-500/10",
  },
];

export default function ActivityPage() {
  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] gap-6">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Live Activity</h1>
          <p className="text-muted-foreground mt-1">
            Real-time feed of all autonomous AI operations across the network.
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-500 text-sm font-medium border border-emerald-500/20">
          <span className="relative flex h-2 w-2 mr-1">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          Live Stream Active
        </div>
      </div>

      <div className="flex-1 rounded-xl border border-border/50 bg-card overflow-hidden shadow-sm flex flex-col">
        <div className="p-4 border-b border-border/50 bg-secondary/30 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-2 font-medium text-sm">
            <Activity className="h-4 w-4 text-indigo-500" /> System Event Log
          </div>
          <Badge variant="secondary" className="font-mono text-xs">5,201 events today</Badge>
        </div>
        
        <ScrollArea className="flex-1 p-6">
          <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border/50 before:to-transparent">
            {MOCK_ACTIVITY.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div key={item.id} className={`relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active`}>
                  
                  {/* Timeline dot */}
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-card ${item.bg} ${item.color} shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 absolute left-0 md:left-1/2 -translate-x-0 md:translate-x-0 z-10`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  
                  {/* Content card */}
                  <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-border/50 bg-secondary/10 hover:bg-secondary/20 transition-colors ml-14 md:ml-0 shadow-sm">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-bold text-sm text-foreground">{item.agent}</h4>
                      <time className="font-mono text-xs text-muted-foreground">{item.time}</time>
                    </div>
                    <div className="text-sm font-medium mb-1">{item.action}</div>
                    <p className="text-sm text-muted-foreground">{item.detail}</p>
                  </div>

                </div>
              );
            })}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
