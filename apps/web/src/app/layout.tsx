import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata={title:"NOMOS ERP",description:"Operations ERP"};

const groups=[
 {label:"Workspace",items:[["Overview","/"],["Approvals","/approvals"],["Reports","/reports"]]},
 {label:"Operations",items:[["Inventory","/inventory"],["Procurement","/procurement"],["Sales & CRM","/sales"],["Partners","/partners"],["CRM Pipeline","/crm"],["Finance","/finance"]]},
 {label:"Master Data",items:[["Products","/products"],["Categories","/categories"],["Units","/units"],["Warehouses","/warehouses"],["Locations","/locations"],["Imports","/imports"]]},
 {label:"Management",items:[["Users & Audit","/admin"],["Plan & Subscription","/settings/subscription"]]},
];
export default function RootLayout({children}:{children:ReactNode}){return <html lang="th"><body><div className="app-shell"><aside className="sidebar"><Link href="/" className="brand"><span className="brand-mark">N</span><span><strong>NOMOS</strong><small>ERP workspace</small></span></Link><nav className="sidebar-nav">{groups.map(g=><div className="nav-group" key={g.label}><div className="nav-label">{g.label}</div>{g.items.map(([label,href])=><Link key={href} href={href}>{label}</Link>)}</div>)}</nav><div className="sidebar-foot"><span className="live-dot"/>System online</div></aside><div className="workspace"><header className="topbar"><div><strong>Operations workspace</strong><span>Private pilot · Host 73</span></div><div className="top-actions"><Link href="/login">Sign in / switch tenant</Link><span className="avatar">NO</span></div></header><div className="content">{children}</div></div></div></body></html>}
