"use client";
import {useCallback,useEffect,useState} from "react";
import {apiError,authHeaders} from "../inventory/client";

type Catalog={code:string;columns:string[]};
type Row=Record<string,string|number|null>;
export default function Reports(){
 const base=process.env.NEXT_PUBLIC_API_URL??"";const [catalog,setCatalog]=useState<Catalog[]>([]),[report,setReport]=useState("management-summary"),[rows,setRows]=useState<Row[]>([]),[error,setError]=useState(""),[loading,setLoading]=useState(false);
 const loadCatalog=useCallback(async()=>{const h=authHeaders();if(!h){setError("กรุณาเข้าสู่ระบบ");return}const r=await fetch(base+"/api/v1/reports",{headers:h});if(!r.ok){setError(await apiError(r));return}setCatalog((await r.json()).data)},[base]);
 const load=useCallback(async()=>{const h=authHeaders();if(!h)return;setLoading(true);setError("");const r=await fetch(base+"/api/v1/reports/"+report+"?limit=200",{headers:h});setLoading(false);if(!r.ok){setError(await apiError(r));return}setRows((await r.json()).data)},[base,report]);
 useEffect(()=>{queueMicrotask(loadCatalog)},[loadCatalog]);useEffect(()=>{queueMicrotask(load)},[load]);
 async function download(format:"csv"|"xlsx"){const h=authHeaders();if(!h)return;const r=await fetch(base+"/api/v1/reports/"+report+"/export?format="+format,{headers:h});if(!r.ok){setError(await apiError(r));return}const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=report+"."+format;a.click();URL.revokeObjectURL(url)}
 const columns=catalog.find(x=>x.code===report)?.columns??Object.keys(rows[0]??{});
 return <main className="erp-main"><div className="page-head"><div><p className="eyebrow">NOMOS ERP · REPORTING</p><h1>Operational Reports</h1><p>Bounded tenant-scoped views across Inventory, Procurement, Sales/CRM and management. Exports use the same server-side report definitions.</p></div></div><section className="panel"><label>Report<select value={report} onChange={e=>setReport(e.target.value)}>{catalog.map(x=><option key={x.code} value={x.code}>{x.code}</option>)}</select></label> <button type="button" onClick={()=>void download("csv")}>Export CSV</button> <button type="button" onClick={()=>void download("xlsx")}>Export XLSX</button></section>{error&&<div className="state error">{error}</div>}{loading?<div className="state">Loading report…</div>:rows.length===0?<div className="state">No rows for this report.</div>:<section className="panel"><div className="table-wrap"><table><thead><tr>{columns.map(c=><th key={c}>{c.replaceAll("_"," ")}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{columns.map(c=><td key={c} className={typeof row[c]==="number"?"mono":undefined}>{row[c]??"—"}</td>)}</tr>)}</tbody></table></div></section>}</main>
}