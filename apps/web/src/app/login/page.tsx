"use client";
import {FormEvent,useEffect,useState} from "react";
import {useRouter} from "next/navigation";

const DEMO_TENANT="11111111-1111-4111-8111-111111111111";
const DEMO_EMAIL="admin@demo.nomos.local";

export default function LoginPage(){
 const router=useRouter();
 const [email,setEmail]=useState(DEMO_EMAIL),[tenant,setTenant]=useState(DEMO_TENANT);
 const [message,setMessage]=useState(""),[busy,setBusy]=useState(false);
 useEffect(()=>{queueMicrotask(()=>{if(sessionStorage.getItem("nomos_session"))setMessage("มีเซสชันอยู่แล้ว — สามารถเข้า Workspace ได้");});},[]);
 async function submit(e:FormEvent){e.preventDefault();setBusy(true);setMessage("กำลังเข้าสู่ระบบ…");
  try{
   const r=await fetch("/api/v1/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password:"",tenant_id:tenant})});
   if(!r.ok){setMessage(r.status===401?"Tenant หรือ Email ไม่ถูกต้อง":"ระบบเข้าสู่ระบบขัดข้อง กรุณาลองใหม่");return}
   const body=await r.json() as {data:{session_token:string;tenant_id:string;permissions:string[]}};
   sessionStorage.setItem("nomos_session",body.data.session_token);sessionStorage.setItem("nomos_tenant",body.data.tenant_id);sessionStorage.setItem("nomos_permissions",JSON.stringify(body.data.permissions));
   setMessage(`เข้าสู่ระบบสำเร็จ · ${body.data.permissions.length} permissions`);router.push("/");router.refresh();
  }catch{setMessage("เชื่อมต่อ ERP API ไม่ได้");}finally{setBusy(false)}
 }
 return <main className="erp-main auth-page"><div className="auth-intro"><p className="eyebrow">NOMOS ERP</p><h1>Operations workspace</h1><p>เข้าสู่ระบบ Demo Tenant เพื่อทดสอบ Inventory, Procurement, Sales/CRM และ Finance บน Host 73</p></div>
 <form className="login-card" onSubmit={submit}><div className="form-title"><strong>Demo sign in</strong><span>Temporary private-pilot access</span></div>
 <label>Tenant ID<input required value={tenant} onChange={e=>setTenant(e.target.value)} autoComplete="organization"/></label>
 <label>Email<input required type="email" value={email} onChange={e=>setEmail(e.target.value)} autoComplete="username"/></label>
 <div className="demo-note">Demo environment นี้ไม่ต้องกรอก Password ชั่วคราว</div>
 <button className="button" disabled={busy} type="submit">{busy?"Signing in…":"Sign in to NOMOS"}</button>
 <p className={message.includes("สำเร็จ")?"success-text":""} aria-live="polite">{message}</p></form></main>
}