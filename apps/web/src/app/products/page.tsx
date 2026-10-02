"use client";

import { FormEvent, useEffect, useState } from "react";

type Product = {id:string;sku:string;name:string;product_type:string;tracking_type:string;status:string};
type Meta = {next_cursor:string|null};

export default function ProductsPage(){
  const [items,setItems]=useState<Product[]>([]);
  const [search,setSearch]=useState("");
  const [status,setStatus]=useState("ACTIVE");
  const [cursor,setCursor]=useState<string|null>(null);
  const [next,setNext]=useState<string|null>(null);
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);

  async function load(nextCursor:string|null=null){
    setLoading(true); setError("");
    const token=sessionStorage.getItem("nomos_session");
    const tenant=sessionStorage.getItem("nomos_tenant");
    if(!token||!tenant){setError("กรุณาเข้าสู่ระบบก่อนใช้งาน Master Data");setLoading(false);return;}
    const q=new URLSearchParams({limit:"50",status});
    if(search) q.set("search",search);
    if(nextCursor) q.set("cursor",nextCursor);
    const response=await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1/products?${q}`,{
      headers:{Authorization:`Bearer ${token}`,"X-Tenant-ID":tenant}
    });
    if(!response.ok){setError("โหลดข้อมูลสินค้าไม่สำเร็จ");setLoading(false);return;}
    const body=await response.json() as {data:Product[];meta:Meta};
    setItems(body.data);setNext(body.meta.next_cursor);setCursor(nextCursor);setLoading(false);
  }
  useEffect(()=>{void load(null);},[]); // eslint-disable-line react-hooks/exhaustive-deps
  function submit(event:FormEvent){event.preventDefault();void load(null)}
  return <main className="erp-main">
    <div className="page-head"><div><p className="eyebrow">MASTER DATA</p><h1>Products</h1><p>Tenant-scoped product catalog, SKU and tracking policy.</p></div><a className="button" href="/">Overview</a></div>
    <form className="filterbar" onSubmit={submit}><label>Search<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="SKU or product name"/></label><label>Status<select value={status} onChange={e=>setStatus(e.target.value)}><option>ACTIVE</option><option>ARCHIVED</option></select></label><button className="button" type="submit">Search</button></form>
    {error&&<div className="state error" role="alert">{error}</div>}
    {loading?<div className="state">Loading…</div>:items.length===0&&!error?<div className="state">No products found.</div>:<div className="table-wrap"><table><thead><tr><th>SKU</th><th>Name</th><th>Type</th><th>Tracking</th><th>Status</th></tr></thead><tbody>{items.map(p=><tr key={p.id}><td className="mono">{p.sku}</td><td>{p.name}</td><td>{p.product_type}</td><td>{p.tracking_type}</td><td><span className="badge">{p.status}</span></td></tr>)}</tbody></table></div>}
    <div className="pager"><button disabled={!cursor} onClick={()=>void load(null)}>First</button><button disabled={!next} onClick={()=>void load(next)}>Next</button></div>
  </main>
}