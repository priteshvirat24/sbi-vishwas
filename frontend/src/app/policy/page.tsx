import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Book, FileText, Scale, ExternalLink } from "lucide-react";

const MOCK_POLICIES = [
  {
    id: "RBI/2023-24/53",
    title: "Master Circular on Customer Service in Banks",
    match: "98%",
    snippet: "...banks are advised that they should not insist on opening of savings bank account or any other product as a precondition for...",
    type: "Mandate",
  },
  {
    id: "SBI/POL/2024-11",
    title: "Zero Balance Account (BSBD) Operating Guidelines",
    match: "92%",
    snippet: "...no minimum balance requirement. Banks cannot levy penalty for non-maintenance of minimum balance...",
    type: "Internal",
  },
  {
    id: "RBI/2022-23/92",
    title: "Fair Practices Code for Lenders",
    match: "75%",
    snippet: "...transparency in respect of terms and conditions of the loans...",
    type: "Guideline",
  }
];

export default function PolicyExplorerPage() {
  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] gap-6">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Policy Explorer</h1>
          <p className="text-muted-foreground mt-1">
            Vector search through the embedded RBI and SBI regulatory knowledge base.
          </p>
        </div>
      </div>

      <div className="flex gap-6 flex-1 min-h-0">
        {/* Search & Results Panel */}
        <div className="w-1/3 flex flex-col gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="E.g. Is insurance mandatory for savings account?" 
              className="pl-9 bg-card border-border/50 h-10"
              defaultValue="Are there minimum balance penalties on zero balance accounts?"
            />
          </div>
          
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Top Matches (Qdrant)</span>
            <Badge variant="secondary" className="text-[10px]">Vector Search</Badge>
          </div>

          <ScrollArea className="flex-1 -mx-1 px-1">
            <div className="space-y-3 pb-4">
              {MOCK_POLICIES.map((doc, i) => (
                <div key={i} className={`p-4 rounded-xl border cursor-pointer transition-all ${i === 1 ? 'border-indigo-500/50 bg-indigo-500/5 shadow-sm' : 'border-border/50 bg-card hover:border-border'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <Badge variant="outline" className={i === 1 ? 'border-indigo-500/30 text-indigo-400' : ''}>{doc.id}</Badge>
                    <span className="text-xs font-mono text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded">{doc.match}</span>
                  </div>
                  <h4 className="font-medium text-sm mb-2">{doc.title}</h4>
                  <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
                    {doc.snippet}
                  </p>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Document Viewer Panel */}
        <div className="w-2/3 rounded-xl border border-border/50 bg-card shadow-sm flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border/50 bg-secondary/30 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-2">
              <Book className="h-4 w-4 text-indigo-500" />
              <span className="font-medium text-sm">SBI/POL/2024-11</span>
            </div>
            <Button variant="ghost" size="sm" className="h-8 text-xs">
              <ExternalLink className="h-3 w-3 mr-2" /> View Original PDF
            </Button>
          </div>
          
          <ScrollArea className="flex-1 p-8">
            <div className="max-w-2xl mx-auto space-y-6">
              <div>
                <h2 className="text-2xl font-bold mb-2">Zero Balance Account (BSBD) Operating Guidelines</h2>
                <div className="flex gap-2">
                  <Badge variant="secondary">Internal Policy</Badge>
                  <Badge variant="secondary">Updated: Jan 2024</Badge>
                </div>
              </div>
              
              <div className="prose prose-sm dark:prose-invert">
                <p>The Basic Savings Bank Deposit (BSBD) Account has been designed as a savings account which will offer certain minimum facilities, free of charge, to the holders of such accounts. The objective is to promote financial inclusion.</p>
                
                <h3>3. Maintenance of Minimum Balance</h3>
                <div className="bg-indigo-500/10 border-l-2 border-indigo-500 p-4 rounded-r-lg my-4">
                  <p className="m-0 text-indigo-100 font-medium">3.1 There shall be no requirement for maintaining any minimum balance in BSBD accounts.</p>
                </div>
                
                <p>3.2 Banks are advised that they should not levy any penal charges for non-maintenance of minimum balances in any basic savings bank deposit account.</p>
                
                <h3>4. Product Bundling</h3>
                <p>4.1 Account opening cannot be made conditional upon the customer purchasing any other product or service (such as life insurance, mutual funds, or credit cards).</p>
                
                <hr className="my-8 border-border/50" />
                
                <div className="flex items-start gap-4 p-4 rounded-xl bg-secondary/20 border border-border/50 mt-8">
                  <Scale className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-sm mb-1">AI Semantic Interpretation</h4>
                    <p className="text-sm text-muted-foreground">The AI engine interprets this document to mean that any deduction labelled "minimum balance penalty" on a BSBD account is an automatic policy violation requiring immediate reversal.</p>
                  </div>
                </div>
              </div>
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}
