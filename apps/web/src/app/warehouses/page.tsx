"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Warehouse={id:string;code:string;name:string;status:string;legal_entity_id:string;branch_id:string|null};

export default function WarehousesPage(){
 const [items,setItems]=useState<Warehouse[]>([]);
 const [error,setError]=useState("");
 useEffect(()=>{queueMicrotask(()=>{
   const token=sessionStorage.getItem("nomos_session");
   const tenant=sessionStorage.getItem("nomos_tenant");
   if(!token||!tenant){setError("กรุณาเข้าสู่ระบบก่อนใช้งาน Master Data");return}
   fetch(`${process.env.NEXT_PUBLIC_API_URL??""}/api/v1/warehouses?status=ACTIVE`,{headers:{Authorization:`Bearer ${token}`,"X-Tenant-ID":tenant}})
     .then(async r=>{if(!r.ok)throw new Error();return r.json()})
     .then(b=>setItems(b.data as Warehouse[]))
     .catch(()=>setError("โหลดข้อมูลคลังไม่สำเร็จ"));
 })},[]);
 return <main className="erp-main"><div className="page-head"><div><p className="eyebrow">MASTER DATA</p><h1>Warehouses</h1><p>Legal-entity owned warehouses and branch assignments.</p></div><Link className="button" href="/">Overview</Link></div>{error&&<div className="state error">{error}</div>}<div className="table-wrap"><table><thead><tr><th>Code</th><th>Name</th><th>Legal entity</th><th>Branch</th><th>Status</th></tr></thead><tbody>{items.map(w=><tr key={w.id}><td className="mono">{w.code}</td><td>{w.name}</td><td className="mono">{w.legal_entity_id.slice(0,8)}</td><td className="mono">{w.branch_id?.slice(0,8)??"—"}</td><td><span className="badge">{w.status}</span></td></tr>)}</tbody></table></div></main>
}