"use client";

import * as React from "react";
import {
  Activity,
  AlertTriangle,
  BookOpen,
  Briefcase,
  History,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  Users,
  Workflow,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const navItems = [
  {
    title: "Command Center",
    url: "/",
    icon: LayoutDashboard,
    group: "Overview",
  },
  {
    title: "Live Activity",
    url: "/activity",
    icon: Activity,
    group: "Overview",
  },
  {
    title: "Customer Journeys",
    url: "/customers",
    icon: Users,
    group: "Operations",
  },
  {
    title: "Agent Workflows",
    url: "/workflows",
    icon: Workflow,
    group: "Operations",
  },
  {
    title: "Human Approvals",
    url: "/approvals",
    icon: AlertTriangle,
    group: "Operations",
  },
  {
    title: "Policy Explorer",
    url: "/policy",
    icon: ShieldCheck,
    group: "Knowledge",
  },
  {
    title: "Knowledge Base",
    url: "/knowledge",
    icon: BookOpen,
    group: "Knowledge",
  },
  {
    title: "Agent Memory",
    url: "/memory",
    icon: History,
    group: "Knowledge",
  },
  {
    title: "Branch Analytics",
    url: "/analytics",
    icon: Briefcase,
    group: "Management",
  },
  {
    title: "Settings",
    url: "/settings",
    icon: Settings,
    group: "Management",
  },
];

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname();
  const router = useRouter();

  // Group items
  const groups = navItems.reduce((acc, item) => {
    if (!acc[item.group]) {
      acc[item.group] = [];
    }
    acc[item.group].push(item);
    return acc;
  }, {} as Record<string, typeof navItems>);

  return (
    <Sidebar {...props}>
      <SidebarHeader className="border-b px-6 py-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div className="flex flex-col gap-0.5 leading-none">
            <span className="font-bold text-base tracking-tight">SBI Vishwas</span>
            <span className="text-[10px] uppercase text-muted-foreground font-semibold tracking-wider">
              AI Command Center
            </span>
          </div>
        </Link>
      </SidebarHeader>
      <SidebarContent className="px-2 pt-4">
        {Object.entries(groups).map(([group, items]) => (
          <SidebarGroup key={group}>
            <SidebarGroupLabel className="text-xs uppercase tracking-wider text-muted-foreground font-semibold px-4">
              {group}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      isActive={pathname === item.url}
                      className="px-4 py-2 transition-colors hover:bg-muted"
                      onClick={() => router.push(item.url)}
                    >
                      <item.icon className="h-4 w-4 mr-2" />
                      <span className="font-medium text-sm">{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
