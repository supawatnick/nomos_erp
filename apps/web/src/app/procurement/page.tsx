"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {apiError,authHeaders,newIdempotencyKey} from "../inventory/client";

type Order={id:string;order_number:string;supplier_id:string;currency_code:string;status:string;version:number};
type Line={id:string;line_number:number;product_id:string;unit_id:string;ordered_quantity:string;received_quantity:string;returned_quantity:string};

export default function Procurement(){
 const [orders,setOrders]=useState<Order[]>([]),[lines,setLines]=useState<Line[]>([]);
 const [selected,setSelected]=useState(""),[location,setLocation]=useState(""),[line,setLine]=useState(""),[qty,setQty]=useState("");
 const [error,setError]=useState(""),[message,setMessage]=useState("");
 const base=process.env.NEXT_PUBLIC_API_URL??"";
 async function load(){const h=authHeaders();if(!h){setError("กรุณาเข้าสู่ระบบ");return}const r=await fetch(base+"/api/v1/procurement/orders",{headers:h});if(!r.ok){setError(await apiError(r));return}setOrders((await r.json()).data)}
 useEffect(()=>{queueMicrotask(load)},[]);
 async function choose(id:string){setSelected(id);setError("");const h=authHeaders();if(!h)return;const r=await fetch(base+`/api/v1/procurement/orders/${id}/lines`,{headers:h});if(!r.ok){setError(await apiError(r));return}setLines((await r.json()).data)}
 async function postMovement(kind:"receipts"|"returns"){setError("");setMessage("");const h=authHeaders();if(!h||!selected||!line)return;const r=await fetch(base+`/api/v1/procurement/orders/${selected}/${kind}`,{method:"POST",headers:{...h,"Content-Type":"application/json","Idempotency-Key":newIdempotencyKey(kind)},body:JSON.stringify({location_id:location,lines:[{purchase_order_line_id:line,quantity:qty}]})});if(!r.ok){setError(await apiError(r));return}setMessage(kind==="receipts"?"Goods Receipt posted":"Purchase Return posted");await load();await choose(selected)}
 return <main className="erp-main"><p className="eyebrow">NOMOS ERP · PROCUREMENT</p><h1>Procurement & Purchasing</h1><p>Purchase Orders, partial receiving and supplier returns. Posted stock effects are committed by Inventory before procurement status advances.</p>
 {error&&<p className="error" role="alert">{error}</p>}{message&&<p aria-live="polite">{message}</p>}
 <section className="panel"><div className="section-head"><h2>Purchase Orders</h2><Link href="/">Operations</Link></div>
 <div className="table-wrap"><table><thead><tr><th>PO</th><th>Supplier</th><th>Status</th><th>Currency</th><th></th></tr></thead><tbody>{orders.map(o=><tr key={o.id}><td>{o.order_number}</td><td className="mono">{o.supplier_id}</td><td><span className="status">{o.status}</span></td><td>{o.currency_code}</td><td><button type="button" onClick={()=>choose(o.id)}>Receive / Return</button></td></tr>)}</tbody></table></div></section>
 {selected&&<section className="panel"><h2>Receipt / Return</h2><p>Choose a PO line and enter the warehouse location. Partial quantities are supported; over-receipt and over-return are rejected server-side.</p>
 <div className="table-wrap"><table><thead><tr><th>Line</th><th>Ordered</th><th>Received</th><th>Returned</th></tr></thead><tbody>{lines.map(x=><tr key={x.id}><td>{x.line_number}</td><td>{x.ordered_quantity}</td><td>{x.received_quantity}</td><td>{x.returned_quantity}</td></tr>)}</tbody></table></div>
 <form className="login-card" onSubmit={e=>{e.preventDefault();void postMovement("receipts")}}><label>Location ID<input required value={location} onChange={e=>setLocation(e.target.value)}/></label><label>PO line<select required value={line} onChange={e=>setLine(e.target.value)}><option value="">Select line</option>{lines.map(x=><option key={x.id} value={x.id}>Line {x.line_number} · remaining {Number(x.ordered_quantity)-Number(x.received_quantity)}</option>)}</select></label><label>Quantity<input required inputMode="decimal" value={qty} onChange={e=>setQty(e.target.value)}/></label><div><button className="button" type="submit">Post Goods Receipt</button> <button type="button" onClick={()=>void postMovement("returns")}>Post Purchase Return</button></div></form></section>}
 </main>
}