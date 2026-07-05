"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AgentExecutionGraph, GraphNode } from "@/components/ai/AgentExecutionGraph";
import { ReasoningTimeline, ReasoningStep } from "@/components/ai/ReasoningTimeline";
import { ArrowLeft, Play, UserCheck, ShieldAlert, FileText } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

// Mock data for the workflow visualization
const mockNodes: GraphNode[] = [
  { id: "1", label: "Input Received", status: "completed" },
  { id: "2", label: "Journey Tracker", agent: "Agent 1", status: "completed" },
  { id: "3", label: "Policy Compliance", agent: "Agent 2", status: "active" },
  { id: "4", label: "Escalation Check", agent: "Agent 4", status: "pending" },
  { id: "5", label: "Resolution", status: "pending" },
];

const mockReasoning: ReasoningStep[] = [
  {
    id: "r1",
    timestamp: "14:32:01",
    title: "Analyzed customer message",
    description: "Customer is requesting a fee waiver for a PMJDY account due to minimum balance deduction.",
    type: "thought",
    status: "completed"
  },
  {
    id: "r2",
    timestamp: "14:32:05",
    title: "Fetched CBS Account Data",
    type: "tool_call",
    status: "completed",
    metadata: {
      tool: "cbs_account_query",
      account_type: "BSBD/PMJDY",
      balance: 142.50,
      recent_deduction: 500.00,
      deduction_code: "MIN_BAL_PENALTY"
    }
  },
  {
    id: "r3",
    timestamp: "14:32:12",
    title: "Checked RBI Policy Knowledge Base",
    type: "tool_call",
    status: "completed",
    metadata: {
      tool: "knowledge_search",
      query: "PMJDY minimum balance penalty rules"
    }
  },
  {
    id: "r4",
    timestamp: "14:32:18",
    title: "Identified Policy Deviation",
    description: "BSBD accounts (including PMJDY) are exempt from minimum balance requirements per RBI master circular. The automated deduction of ₹500 is a system error.",
    type: "observation",
    status: "completed"
  },
  {
    id: "r5",
    timestamp: "14:32:20",
    title: "Requesting Human Approval for Reversal",
    description: "Confidence is high (98%), but financial reversals require Branch Manager approval.",
    type: "decision",
    status: "running"
  }
];

export default function WorkflowDetail() {
  const params = useParams();
  
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" asChild>
            <Link href="/workflows">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">Workflow {params.id}</h1>
              <Badge variant="secondary" className="bg-blue-100 text-blue-700 hover:bg-blue-100">In Progress</Badge>
            </div>
            <p className="text-muted-foreground text-sm">Fee Waiver Request - Customer ID: 9812-3312</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><FileText className="h-4 w-4 mr-2" /> View Transcript</Button>
          <Button className="bg-orange-500 hover:bg-orange-600"><UserCheck className="h-4 w-4 mr-2" /> Review Action</Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Left Column: Graph & Details */}
        <div className="md:col-span-2 flex flex-col gap-6">
          <Card className="border-border/50 shadow-sm overflow-hidden">
            <CardHeader className="bg-secondary/20 pb-4 border-b border-border/50">
              <CardTitle className="text-base">LangGraph Execution Path</CardTitle>
              <CardDescription>Live state transitions of the multi-agent system</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <AgentExecutionGraph nodes={mockNodes} />
            </CardContent>
          </Card>

          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-orange-500" />
                Pending Human Approval
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg border border-orange-200 bg-orange-50/50 p-4">
                <h4 className="font-semibold text-orange-800 mb-2">Automated Fee Reversal Proposed</h4>
                <p className="text-sm text-orange-700 mb-4">
                  The Policy Compliance Agent identified an incorrect minimum balance deduction of ₹500 on a BSBD account. It proposes an immediate reversal and an apology SMS to the customer.
                </p>
                <div className="flex gap-2">
                  <Button size="sm" className="bg-orange-600 hover:bg-orange-700">Approve Reversal</Button>
                  <Button size="sm" variant="outline" className="border-orange-200 text-orange-700 hover:bg-orange-100">Modify Resolution</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Reasoning Timeline */}
        <div className="md:col-span-1">
          <Card className="border-border/50 shadow-sm h-full">
            <CardHeader className="pb-4">
              <CardTitle className="text-base">Agent Reasoning Log</CardTitle>
              <CardDescription>Step-by-step thoughts and tool calls</CardDescription>
            </CardHeader>
            <CardContent>
              <ReasoningTimeline steps={mockReasoning} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
