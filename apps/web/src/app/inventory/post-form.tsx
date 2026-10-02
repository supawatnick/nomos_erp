"use client";
import Link from "next/link";
import {FormEvent,useEffect,useMemo,useState} from "react";
import {apiError,authHeaders,newIdempotencyKey} from "./client";

type Kind="RECEIVE"|"ISSUE"|"TRANSFER"|"ADJUST";
type Product={id:string;sku:string;name:string;base_unit_id:string;product_type:string;status:string};
type Location={id:string;warehouse_id:string;code:string;name:string;allow_stock:boolean;status:string};
type Warehouse={id:string;legal_entity_id:string;branch_id:string|null;code:string;name:string;status:string};
type Props={kind:Kind};

export default function InventoryPostForm({kind}:Props){
 const [products,setProducts]=useState<Product[]>([]);const [locations,setLocations]=useState<Location[]>([]);const [warehouses,setWarehouses]=useState<Warehouse[]>([]);
 const [productId,setProductId]=useState("");const [locationId,setLocationId]=useState("");const [destination,setDestination]=useState("");
 const [quantity,setQuantity]=useState("");const [reference,setReference]=useState("");const [reason,setReason]=useState("");
 const [adjustDirection,setAdjustDirection]=useState("1");const [error,setError]=useState("");const [success,setSuccess]=useState("");
 const [loading,setLoading]=useState(true);const [submitting,setSubmitting]=useState(false);const [retryKey,setRetryKey]=useState<string|null>(null);
 const product=products.find(x=>x.id===productId);const location=locations.find(x=>x.id===locationId);const warehouse=warehouses.find(x=>x.id===location?.warehouse_id);
 const destinations=useMemo(()=>locations.filter(x=>x.id!==locationId&&x.allow_stock&&x.status==="ACTIVE"),[locations,locationId]);
 useEffect(()=>{queueMicrotask(async()=>{const headers=authHeaders();if(!headers){setError("กรุณาเข้าสู่ระบบก่อนทำรายการ Inventory");setLoading(false);return}
  try{const [p,l,w]=await Promise.all([
   fetch(`${process.env.NEXT_PUBLIC_API_URL??""}/api/v1/products?status=ACTIVE&limit=200&sort=sku`,{headers}),
   fetch(`${process.env.NEXT_PUBLIC_API_URL??""}/api/v1/locations`,{headers}),
   fetch(`${process.env.NEXT_PUBLIC_API_URL??""}/api/v1/warehouses?status=ACTIVE&limit=200`,{headers})
  ]);for(const r of [p,l,w])if(!r.ok)throw new Error(await apiError(r));
  setProducts(((await p.json()).data as Product[]).filter(x=>x.product_type!=="SERVICE"));
  setLocations(((await l.json()).data as Location[]).filter(x=>x.allow_stock&&x.status==="ACTIVE"));
  setWarehouses((await w.json()).data as Warehouse[]);
  }catch(e){setError(e instanceof Error?e.message:"โหลดข้อมูลสำหรับทำรายการไม่สำเร็จ")}finally{setLoading(false)}})},[]);
 async function submit(event:FormEvent){event.preventDefault();setError("");setSuccess("");
  if(!product||!location||!warehouse){setError("กรุณาเลือกสินค้าและ Location");return}
  if(kind==="TRANSFER"&&!destination){setError("กรุณาเลือก Destination Location");return}
  const headers=authHeaders();if(!headers){setError("กรุณาเข้าสู่ระบบใหม่");return}
  const key=retryKey??newIdempotencyKey(kind);setRetryKey(key);setSubmitting(true);
  const line:{product_id:string;unit_id:string;location_id:string;quantity:string;destination_location_id?:string;adjustment_direction?:number}={product_id:product.id,unit_id:product.base_unit_id,location_id:location.id,quantity};
  if(kind==="TRANSFER")line.destination_location_id=destination;if(kind==="ADJUST")line.adjustment_direction=Number(adjustDirection);
  try{const r=await fetch(`${process.env.NEXT_PUBLIC_API_URL??""}/api/v1/inventory/transactions`,{method:"POST",headers:{...headers,"Content-Type":"application/json","Idempotency-Key":key},body:JSON.stringify({transaction_type:kind,legal_entity_id:warehouse.legal_entity_id,branch_id:warehouse.branch_id,lines:[line],reference:reference||null,reason:reason||null,source_type:"WEB_MANUAL"})});
   if(!r.ok){setError(await apiError(r));return}const body=await r.json() as {data:{id:string}};setSuccess(`POSTED · ${body.data.id}`);setRetryKey(null);setQuantity("");setReference("");setReason("");
  }catch{setError("การเชื่อมต่อขัดข้อง สามารถกด Retry ได้โดยระบบจะใช้ Idempotency-Key เดิมเพื่อป้องกันการลงสต็อกซ้ำ");}finally{setSubmitting(false)}
 }
 const title={RECEIVE:"Receive Stock",ISSUE:"Issue Stock",TRANSFER:"Transfer Stock",ADJUST:"Adjust Stock"}[kind];
 return <main className="erp-main"><div className="page-head"><div><p className="eyebrow">INVENTORY · {kind}</p><h1>{title}</h1><p>Posts through the authoritative inventory engine. The Web does not calculate or mutate balances directly.</p></div><Link className="button secondary" href="/inventory">Inventory</Link></div>
 {loading?<div className="state">Loading posting context…</div>:<form className="posting-form" onSubmit={e=>void submit(e)}>
 <div className="form-grid"><label>Product<select required value={productId} onChange={e=>setProductId(e.target.value)}><option value="">Select product</option>{products.map(x=><option key={x.id} value={x.id}>{x.sku} · {x.name}</option>)}</select></label>
 <label>Source Location<select required value={locationId} onChange={e=>{setLocationId(e.target.value);setDestination("")}}><option value="">Select location</option>{locations.map(x=><option key={x.id} value={x.id}>{x.code} · {x.name}</option>)}</select></label>
 {kind==="TRANSFER"&&<label>Destination Location<select required value={destination} onChange={e=>setDestination(e.target.value)}><option value="">Select destination</option>{destinations.map(x=><option key={x.id} value={x.id}>{x.code} · {x.name}</option>)}</select></label>}
 {kind==="ADJUST"&&<label>Direction<select value={adjustDirection} onChange={e=>setAdjustDirection(e.target.value)}><option value="1">Increase (+)</option><option value="-1">Decrease (−)</option></select></label>}
 <label>Quantity<input required inputMode="decimal" value={quantity} onChange={e=>setQuantity(e.target.value)} placeholder="0"/></label><label>Reference<input value={reference} onChange={e=>setReference(e.target.value)} placeholder="Document or note"/></label>
 <label className="wide">Reason<input value={reason} onChange={e=>setReason(e.target.value)} placeholder={kind==="ADJUST"?"Required by operating policy":"Optional operational reason"}/></label></div>
 <div className="posting-context"><span>Legal entity</span><strong className="mono">{warehouse?.legal_entity_id.slice(0,8)??"—"}</strong><span>Warehouse</span><strong>{warehouse?.code??"—"}</strong><span>Base unit</span><strong className="mono">{product?.base_unit_id.slice(0,8)??"—"}</strong></div>
 {error&&<div className="state error" role="alert">{error}</div>}{success&&<div className="state success" role="status">{success} · <Link href="/inventory/movements">View movement</Link></div>}
 <div className="form-actions"><button className="button" disabled={submitting||!!success} type="button" onClick={e=>void submit(e as unknown as FormEvent)}>{submitting?"Posting…":retryKey?"Retry safely":"Post "+kind}</button>{retryKey&&<span className="hint">Retry uses the same Idempotency-Key.</span>}</div>
 </form>}</main>
}