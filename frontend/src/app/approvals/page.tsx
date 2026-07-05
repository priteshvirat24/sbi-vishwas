import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Check, X, ShieldAlert } from "lucide-react";

const MOCK_APPROVALS = [
  {
    id: "APP-9921",
    customer: "Rahul Sharma",
    action: "Fee Waiver Request (₹500)",
    reason: "Judge Agent rejected resolution due to unfair minimum balance penalty deduction on a zero-balance account. Advocating for immediate refund.",
    confidence: "98%",
    riskLevel: "Low",
    timeWaiting: "5m",
  },
  {
    id: "APP-9922",
    customer: "Priya Patel",
    action: "Branch Manager Escalation",
    reason: "Customer Advocate detected looping (forwarded 4 times) regarding dormant account. Recommending immediate Level 2 escalation to bypass branch.",
    confidence: "92%",
    riskLevel: "Medium",
    timeWaiting: "12m",
  }
];

export default function ApprovalsPage() {
  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Human Approvals</h1>
        <p className="text-muted-foreground mt-1">
          Review critical actions halted by the AI Judge or Audit Guardian.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {MOCK_APPROVALS.map((approval) => (
          <Card key={approval.id} className="border-border/50 bg-card/50 backdrop-blur-sm shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-4 border-b border-border/50">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-orange-500" />
                    <CardTitle className="text-lg">{approval.action}</CardTitle>
                  </div>
                  <CardDescription className="font-mono text-xs mt-1">{approval.id} • {approval.customer}</CardDescription>
                </div>
                <Badge variant="outline" className="bg-orange-500/10 text-orange-500 border-orange-500/20">
                  {approval.timeWaiting} waiting
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">AI Reasoning</h4>
                  <p className="text-sm leading-relaxed">{approval.reason}</p>
                </div>
                <div className="flex gap-4">
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Confidence</h4>
                    <span className="text-sm font-semibold text-emerald-500">{approval.confidence}</span>
                  </div>
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Risk Level</h4>
                    <span className="text-sm font-semibold">{approval.riskLevel}</span>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="pt-4 border-t border-border/50 flex gap-3">
              <Button className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white">
                <Check className="mr-2 h-4 w-4" /> Approve Action
              </Button>
              <Button variant="outline" className="flex-1 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30">
                <X className="mr-2 h-4 w-4" /> Reject & Reroute
              </Button>
            </CardFooter>
          </Card>
        ))}

        {MOCK_APPROVALS.length === 0 && (
          <div className="col-span-2 p-12 text-center border border-dashed rounded-xl border-border/50 bg-secondary/10 flex flex-col items-center justify-center">
            <div className="h-12 w-12 rounded-full bg-emerald-500/10 flex items-center justify-center mb-4">
              <Check className="h-6 w-6 text-emerald-500" />
            </div>
            <h3 className="text-lg font-medium">All Caught Up</h3>
            <p className="text-sm text-muted-foreground mt-1">No pending actions require human authorization at this time.</p>
          </div>
        )}
      </div>
    </div>
  );
}
