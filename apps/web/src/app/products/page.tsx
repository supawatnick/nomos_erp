"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
type Choice={id:string;code:string;name:string;status:string};

type Product = {id:string;sku:string;name:string;product_type:string;tracking_type:string;status:string};
type Meta = {next_cursor:string|null};

export default function ProductsPage(){
  const [items,setItems]=useState<Product[]>([]);
  const [search,setSearch]=useState("");
  const [status,setStatus]=useState("ACTIVE");
  const [sort,setSort]=useState("id");
  const [cursor,setCursor]=useState<string|null>(null);
  const [next,setNext]=useState<string|null>(null);
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);\n  const [units,setUnits]=useState<Choice[]>([]),[categories,setCategories]=useState<Choice[]>([]);\n  const [sku,setSku]=useState(""),[name,setName]=useState(""),[baseUnitId,setBaseUnitId]=useState(""),[categoryId,setCategoryId]=useState(""),[productType,setProductType]=useState("STOCK"),[trackingType,setTrackingType]=useState("NONE"),[saving,setSaving]=useState(false);

  async function load(nextCursor:string|null=null){
    setLoading(true); setError("");
    const token=sessionStorage.getItem("nomos_session");
    const tenant=sessionStorage.getItem("nomos_tenant");
    if(!token||!tenant){setError("กรุณาเข้าสู่ระบบก่อนใช้งาน Master Data");setLoading(false);return;}
    const q=new URLSearchParams({limit:"50",status,sort});
    if(search) q.set("search",search);
    if(nextCursor) q.set("cursor",nextCursor);
    const response=await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1/products?${q}`,{
      headers:{Authorization:`Bearer ${token}`,"X-Tenant-ID":tenant}
    });
    if(!response.ok){setError("โหลดข้อมูลสินค้าไม่สำเร็จ");setLoading(false);return;}
    const body=await response.json() as {data:Product[];meta:Meta};
    setItems(body.data);setNext(body.meta.next_cursor);setCursor(nextCursor);setLoading(false);
  }
  useEffect(()=>{queueMicrotask(()=>{void load(null);const token=sessionStorage.getItem("nomos_session"),tenant=sessionStorage.getItem("nomos_tenant");if(!token||!tenant)return;const headers={Authorization:`Bearer ${token}`,"X-Tenant-ID":tenant};Promise.all([fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1/units`,{headers}),fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1/categories`,{headers})]).then(async([u,c])=>{if(!u.ok||!c.ok)throw new Error();const ub=await u.json(),cb=await c.json();setUnits(ub.data);setCategories(cb.data);if(ub.data[0])setBaseUnitId(ub.data[0].id)}).catch(()=>setError("โหลดข้อมูลอ้างอิงสินค้าไม่สำเร็จ"))});},[]); // eslint-disable-line react-hooks/exhaustive-deps
  function submit(event:FormEvent){event.preventDefault();void load(null)}\n  async function createProduct(event:FormEvent){event.preventDefault();const token=sessionStorage.getItem("nomos_session"),tenant=sessionStorage.getItem("nomos_tenant");if(!token||!tenant||!baseUnitId)return;setSaving(true);setError("");const r=await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1/products`,{method:"POST",headers:{Authorization:`Bearer ${token}`,"X-Tenant-ID":tenant,"Content-Type":"application/json"},body:JSON.stringify({sku:sku.trim(),name:name.trim(),product_type:productType,base_unit_id:baseUnitId,category_id:categoryId||null,tracking_type:trackingType})});setSaving(false);if(!r.ok){setError(r.status===409?"SKU already exists.":"สร้าง Product ไม่สำเร็จ");return}setSku("");setName("");await load(null)}\n  async function archiveProduct(id:string){const token=sessionStorage.getItem("nomos_session"),tenant=sessionStorage.getItem("nomos_tenant");if(!token||!tenant||!confirm("Archive this product?"))return;const r=await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1/products/${id}/archive`,{method:"POST",headers:{Authorization:`Bearer ${token}`,"X-Tenant-ID":tenant}});if(!r.ok){setError("Archive Product ไม่สำเร็จ");return}await load(null)}
  return <main className="erp-main">
    <div className="page-head"><div><p className="eyebrow">MASTER DATA</p><h1>Products</h1><p>Tenant-scoped product catalog, SKU and tracking policy.</p></div><Link className="button" href="/">Overview</Link></div>
    <form className="filterbar" onSubmit={createProduct}><label>SKU<input required maxLength={100} value={sku} onChange={e=>setSku(e.target.value)}/></label><label>Name<input required maxLength={240} value={name} onChange={e=>setName(e.target.value)}/></label><label>Type<select value={productType} onChange={e=>setProductType(e.target.value)}><option value="STOCK">STOCK</option><option value="SERVICE">SERVICE</option></select></label><label>Base unit<select required value={baseUnitId} onChange={e=>setBaseUnitId(e.target.value)}>{units.filter(x=>x.status==="ACTIVE").map(x=><option key={x.id} value={x.id}>{x.code} · {x.name}</option>)}</select></label><label>Category<select value={categoryId} onChange={e=>setCategoryId(e.target.value)}><option value="">—</option>{categories.filter(x=>x.status==="ACTIVE").map(x=><option key={x.id} value={x.id}>{x.code} · {x.name}</option>)}</select></label><label>Tracking<select value={trackingType} onChange={e=>setTrackingType(e.target.value)}><option>NONE</option><option>LOT</option><option>SERIAL</option></select></label><button className="button" disabled={saving||!baseUnitId} type="submit">{saving?"Creating…":"Create Product"}</button></form>\n    <form className="filterbar" onSubmit={submit}><label>Search<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="SKU or product name"/></label><label>Status<select value={status} onChange={e=>setStatus(e.target.value)}><option>ACTIVE</option><option>ARCHIVED</option></select></label><label>Sort<select value={sort} onChange={e=>setSort(e.target.value)}><option value="id">Created</option><option value="sku">SKU</option><option value="name">Name</option><option value="updated_at">Updated</option></select></label><button className="button" type="submit">Search</button></form>
    {error&&<div className="state error" role="alert">{error}</div>}
    {loading?<div className="state">Loading…</div>:items.length===0&&!error?<div className="state">No products found.</div>:<div className="table-wrap"><table><thead><tr><th>SKU</th><th>Name</th><th>Type</th><th>Tracking</th><th>Status</th><th>Action</th></tr></thead><tbody>{items.map(p=><tr key={p.id}><td className="mono">{p.sku}</td><td>{p.name}</td><td>{p.product_type}</td><td>{p.tracking_type}</td><td><span className="badge">{p.status}</span></td><td>{p.status==="ACTIVE"?<button type="button" onClick={()=>void archiveProduct(p.id)}>Archive</button>:"—"}</td></tr>)}</tbody></table></div>}
    <div className="pager"><button disabled={!cursor} onClick={()=>void load(null)}>First</button><button disabled={!next} onClick={()=>void load(next)}>Next</button></div>
  </main>
}