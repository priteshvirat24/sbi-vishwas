"use client";

import { Activity, AlertCircle, ArrowUpRight, CheckCircle2, Clock, ShieldAlert, Users, Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Progress } from "@/components/ui/progress";

const agentActivityData = [
  { time: "08:00", interactions: 120 },
  { time: "09:00", interactions: 240 },
  { time: "10:00", interactions: 310 },
  { time: "11:00", interactions: 450 },
  { time: "12:00", interactions: 380 },
  { time: "13:00", interactions: 290 },
  { time: "14:00", interactions: 410 },
];

const pendingApprovals = [
  { id: "APP-0921", agent: "Escalation Advocate", customer: "Rajesh Kumar", reason: "Account Unfreeze", confidence: 0.65 },
  { id: "APP-0922", agent: "Policy Compliance", customer: "Anjali Gupta", reason: "Fee Waiver Request", confidence: 0.71 },
  { id: "APP-0923", agent: "Diagnosis Agent", customer: "Priya Sharma", reason: "Complex Transaction Dispute", confidence: 0.58 },
];

export default function Dashboard() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">AI Command Center</h1>
        <p className="text-muted-foreground">Monitor live agent activity and system health.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Zap className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">42</div>
            <p className="text-xs text-muted-foreground flex items-center mt-1">
              <ArrowUpRight className="h-3 w-3 mr-1 text-emerald-500" />
              <span className="text-emerald-500 font-medium">12%</span> from last hour
            </p>
          </CardContent>
        </Card>
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Live Interactions</CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,204</div>
            <p className="text-xs text-muted-foreground flex items-center mt-1">
              Across 5 active channels
            </p>
          </CardContent>
        </Card>
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Auto-Resolution Rate</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">94.2%</div>
            <Progress value={94.2} className="h-2 mt-2" />
          </CardContent>
        </Card>
        <Card className="border-border/50 shadow-sm bg-primary text-primary-foreground">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
            <Clock className="h-4 w-4 opacity-80" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs opacity-80 mt-1">
              Require human intervention
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        <Card className="md:col-span-4 border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle>Agent Interactions Timeline</CardTitle>
            <CardDescription>Live volume of autonomous agent operations</CardDescription>
          </CardHeader>
          <CardContent className="px-2">
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={agentActivityData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorInteractions" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00AEEF" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#00AEEF" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                  <Tooltip
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="interactions"
                    stroke="#00AEEF"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorInteractions)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-3 border-border/50 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Human in the Loop</CardTitle>
              <CardDescription>Tasks requiring manual review</CardDescription>
            </div>
            <Badge variant="destructive" className="bg-orange-500 hover:bg-orange-600">Action Required</Badge>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-4">
                {pendingApprovals.map((approval) => (
                  <div key={approval.id} className="flex flex-col gap-2 p-3 rounded-lg border border-border/50 bg-secondary/20 transition-colors hover:bg-secondary/40 cursor-pointer">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold">{approval.id}</span>
                      <span className="text-xs text-muted-foreground">{approval.agent}</span>
                    </div>
                    <p className="text-sm">{approval.reason}</p>
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center gap-2">
                        <Users className="h-3 w-3 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">{approval.customer}</span>
                      </div>
                      <Badge variant="outline" className="text-[10px] font-normal border-orange-200 text-orange-600 bg-orange-50">
                        Conf: {(approval.confidence * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
