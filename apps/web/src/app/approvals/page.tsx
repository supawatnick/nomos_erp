"use client";
import {useCallback,useEffect,useState} from "react";
import {apiError,authHeaders,newIdempotencyKey} from "../inventory/client";

type Approval={id:string;request_type:string;source_type:string;source_id:string;source_version:number|null;status:string;current_step:number;steps_required:number;policy_code:string;policy_name:string;expires_at:string|null;created_at:string};

export default function Approvals(){
 const [rows,setRows]=useState<Approval[]>([]),[error,setError]=useState(""),[message,setMessage]=useState("");
 const base=process.env.NEXT_PUBLIC_API_URL??"";
 const load=useCallback(async()=>{const h=authHeaders();if(!h){setError("กรุณาเข้าสู่ระบบ");return}const r=await fetch(base+"/api/v1/approvals",{headers:h});if(!r.ok){setError(await apiError(r));return}setRows((await r.json()).data)},[base]);
 useEffect(()=>{queueMicrotask(load)},[load]);
 async function decide(id:string,decision:"APPROVED"|"REJECTED"){setError("");setMessage("");const h=authHeaders();if(!h)return;const r=await fetch(base+"/api/v1/approvals/"+id+"/decide",{method:"POST",headers:{...h,"Content-Type":"application/json","Idempotency-Key":newIdempotencyKey("approval")},body:JSON.stringify({decision})});if(!r.ok){setError(await apiError(r));return}setMessage("Decision committed");await load()}
 async function cancel(id:string){const h=authHeaders();if(!h)return;const r=await fetch(base+"/api/v1/approvals/"+id+"/cancel",{method:"POST",headers:h});if(!r.ok){setError(await apiError(r));return}setMessage("Approval cancelled");await load()}
 return <main className="erp-main"><p className="eyebrow">NOMOS ERP · CONTROL</p><h1>Approval Inbox</h1><p>Decisions are server-authorized at the current step. Approved requests remain bound to the original business version and fingerprint until execution.</p>{error&&<p className="error" role="alert">{error}</p>}{message&&<p aria-live="polite">{message}</p>}<section className="panel"><div className="table-wrap"><table><thead><tr><th>Policy</th><th>Request</th><th>Source</th><th>Step</th><th>Status</th><th>Expires</th><th>Actions</th></tr></thead><tbody>{rows.map(x=><tr key={x.id}><td>{x.policy_name}<br/><span className="mono">{x.policy_code}</span></td><td>{x.request_type}</td><td>{x.source_type}<br/><span className="mono">{x.source_id}</span></td><td>{x.current_step}/{x.steps_required}</td><td><span className="status">{x.status}</span></td><td>{x.expires_at?new Date(x.expires_at).toLocaleString():"—"}</td><td>{x.status==="PENDING"?<><button type="button" onClick={()=>void decide(x.id,"APPROVED")}>Approve</button> <button type="button" onClick={()=>void decide(x.id,"REJECTED")}>Reject</button> <button type="button" onClick={()=>void cancel(x.id)}>Cancel</button></>:"—"}</td></tr>)}</tbody></table></div></section></main>
}