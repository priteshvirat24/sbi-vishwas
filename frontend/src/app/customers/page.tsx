import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Users, Search, MoreHorizontal } from "lucide-react";

const MOCK_JOURNEYS = [
  {
    id: "CJ-8901",
    customer: "Rahul Sharma",
    topic: "Forced Insurance Complaint",
    agent: "Customer Advocate",
    status: "Resolving",
    urgency: "Critical",
    time: "2m ago",
  },
  {
    id: "CJ-8902",
    customer: "Priya Patel",
    topic: "Dormant Account Reactivation",
    agent: "Diagnosis Agent",
    status: "Processing",
    urgency: "High",
    time: "15m ago",
  },
  {
    id: "CJ-8903",
    customer: "Amit Kumar",
    topic: "Credit Card Delivery Delay",
    agent: "Journey Tracker",
    status: "Waiting on Customer",
    urgency: "Medium",
    time: "1h ago",
  },
  {
    id: "CJ-8904",
    customer: "Sneha Reddy",
    topic: "Unexplained Fee Deduction",
    agent: "Policy Compliance",
    status: "Auditing",
    urgency: "High",
    time: "2h ago",
  },
];

export default function CustomersPage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Customer Journeys</h1>
          <p className="text-muted-foreground mt-1">
            Live overview of all active AI-managed customer interactions.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="search"
              placeholder="Search journeys..."
              className="flex h-10 w-[250px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pl-9"
            />
          </div>
          <Button className="bg-indigo-600 hover:bg-indigo-700 text-white">
            <Users className="mr-2 h-4 w-4" /> New Journey
          </Button>
        </div>
      </div>

      <div className="rounded-xl border border-border/50 bg-card text-card-foreground shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-secondary/30">
            <TableRow>
              <TableHead className="w-[100px]">ID</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Current Topic</TableHead>
              <TableHead>Active Agent</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Urgency</TableHead>
              <TableHead className="text-right">Last Updated</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {MOCK_JOURNEYS.map((journey) => (
              <TableRow key={journey.id} className="hover:bg-secondary/20 transition-colors">
                <TableCell className="font-medium font-mono text-xs">{journey.id}</TableCell>
                <TableCell className="font-medium">{journey.customer}</TableCell>
                <TableCell>{journey.topic}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                    </span>
                    {journey.agent}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="bg-secondary/50">{journey.status}</Badge>
                </TableCell>
                <TableCell>
                  <Badge 
                    variant={journey.urgency === 'Critical' ? 'destructive' : journey.urgency === 'High' ? 'default' : 'secondary'}
                    className={journey.urgency === 'High' ? 'bg-orange-500 hover:bg-orange-600' : ''}
                  >
                    {journey.urgency}
                  </Badge>
                </TableCell>
                <TableCell className="text-right text-muted-foreground">{journey.time}</TableCell>
                <TableCell>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
