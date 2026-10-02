"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {apiError,authHeaders} from "./client";

type Balance={product_id:string;sku:string;product_name:string;location_id:string;location_code:string;warehouse_code:string;on_hand:string};
type Movement={id:string;transaction_type:string;status:string;reference:string|null;posted_at:string};

export default function InventoryPage(){
 const [balances,setBalances]=useState<Balance[]>([]);const [moves,setMoves]=useState<Movement[]>([]);
 const [error,setError]=useState("");const [loading,setLoading]=useState(true);
 useEffect(()=>{queueMicrotask(async()=>{const headers=authHeaders();if(!headers){setError("กรุณาเข้าสู่ระบบก่อนใช้งาน Inventory");setLoading(false);return}
   try{const [b,m]=await Promise.all([
    fetch(`${process.env.NEXT_PUBLIC_API_URL??""}/api/v1/inventory/balances`,{headers}),
    fetch(`${process.env.NEXT_PUBLIC_API_URL??""}/api/v1/inventory/transactions`,{headers})
   ]);if(!b.ok)throw new Error(await apiError(b));if(!m.ok)throw new Error(await apiError(m));
   setBalances((await b.json()).data as Balance[]);setMoves((await m.json()).data as Movement[]);
   }catch(e){setError(e instanceof Error?e.message:"โหลด Inventory ไม่สำเร็จ")}finally{setLoading(false)}})},[]);
 const total=balances.reduce((sum,row)=>sum+Number(row.on_hand),0);
 return <main className="erp-main"><div className="page-head"><div><p className="eyebrow">INVENTORY</p><h1>Inventory Control</h1><p>Current stock, recent movements and operational posting workflows.</p></div><Link className="button secondary" href="/">Overview</Link></div>
 <nav className="section-nav"><Link href="/inventory/stock">Stock</Link><Link href="/inventory/movements">Movements</Link><Link href="/inventory/receive">Receive</Link><Link href="/inventory/issue">Issue</Link><Link href="/inventory/transfer">Transfer</Link><Link href="/inventory/adjust">Adjust</Link></nav>
 {error&&<div className="state error" role="alert">{error}</div>}{loading?<div className="state">Loading inventory…</div>:!error&&<>
 <div className="metrics"><div className="metric"><span>Balance rows</span><strong>{balances.length}</strong></div><div className="metric"><span>Total base units</span><strong>{total.toLocaleString()}</strong></div><div className="metric"><span>Recent movements</span><strong>{moves.length}</strong></div></div>
 <div className="split"><section className="panel"><div className="panel-head"><h2>Stock snapshot</h2><Link href="/inventory/stock">View all</Link></div>{balances.length===0?<div className="state compact">No stock posted yet.</div>:<table><thead><tr><th>SKU</th><th>Location</th><th>On hand</th></tr></thead><tbody>{balances.slice(0,6).map(x=><tr key={x.product_id+x.location_id}><td><strong>{x.sku}</strong><small>{x.product_name}</small></td><td>{x.warehouse_code} / {x.location_code}</td><td className="quantity">{x.on_hand}</td></tr>)}</tbody></table>}</section>
 <section className="panel"><div className="panel-head"><h2>Recent movements</h2><Link href="/inventory/movements">View all</Link></div>{moves.length===0?<div className="state compact">No movements yet.</div>:<div className="movement-list">{moves.slice(0,6).map(x=><div className="movement" key={x.id}><span className="badge">{x.transaction_type}</span><div><strong>{x.reference??"No reference"}</strong><small>{new Date(x.posted_at).toLocaleString()}</small></div></div>)}</div>}</section></div></>}
 </main>
}