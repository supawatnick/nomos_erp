"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
type Context={actor_user_id:string;tenant_id:string;permissions:string[]};
const modules=[
 ["Inventory","/inventory","Stock, movements and warehouse operations"],
 ["Procurement","/procurement","Purchase orders, receipts and supplier returns"],
 ["Sales & CRM","/sales","Quotations, orders, reservations and fulfillment"],
 ["Finance","/finance","Accounts, journals and AR/AP controls"],
 ["Approvals","/approvals","Commercial policy decisions and controls"],
 ["Reports","/reports","Bounded operational reporting and exports"],
];
export default function Home(){
 const [ctx,setCtx]=useState<Context|null>(null),[state,setState]=useState<"checking"|"guest"|"ready">("checking");
 useEffect(()=>{queueMicrotask(()=>{const token=sessionStorage.getItem("nomos_session"),tenant=sessionStorage.getItem("nomos_tenant");if(!token||!tenant){setState("guest");return}fetch("/api/v1/auth/context",{headers:{Authorization:`Bearer ${token}`,"X-Tenant-ID":tenant}}).then(async r=>{if(!r.ok)throw new Error();const b=await r.json() as {data:Context};setCtx(b.data);setState("ready")}).catch(()=>{sessionStorage.removeItem("nomos_session");sessionStorage.removeItem("nomos_tenant");setState("guest")});});},[]);
 return <main className="erp-main"><div className="page-head"><div><p className="eyebrow">Operations overview</p><h1>ERP workspace</h1><p>Inventory, procurement, sales, finance and management controls in one tenant-safe workspace.</p></div><Link className="button secondary" href="/login">{state==="ready"?"Switch tenant":"Sign in"}</Link></div>
 {state==="checking"&&<div className="state">Checking session…</div>}
 {state==="guest"&&<div className="state callout"><strong>Sign in required</strong><p>ใช้ Demo Tenant เพื่อเปิดข้อมูลและ workflow ของ ERP</p><Link className="button" href="/login">Open demo sign in</Link></div>}
 {state==="ready"&&ctx&&<><div className="metrics"><div className="metric"><span>Session</span><strong>Active</strong></div><div className="metric"><span>Permissions</span><strong>{ctx.permissions.length}</strong></div><div className="metric"><span>Tenant</span><strong className="metric-id">{ctx.tenant_id.slice(0,8)}</strong></div></div><div className="cards">{modules.map(([name,href,desc])=><Link className="card featured" href={href} key={href}><strong>{name}</strong><span>{desc}</span><em>Open workspace →</em></Link>)}</div><div className="section-block"><div className="section-head bare"><div><p className="eyebrow">Administration</p><h2>Master data & controls</h2></div></div><div className="quick-links">{[["Products","/products"],["Warehouses","/warehouses"],["Locations","/locations"],["Partners","/partners"],["CRM Pipeline","/crm"],["Users & Audit","/admin"],["Imports","/imports"],["Subscription","/settings/subscription"]].map(([x,h])=><Link href={h} key={h}>{x}<span>→</span></Link>)}</div></div></>}
 </main>
}