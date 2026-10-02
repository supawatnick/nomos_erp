"use client";

export type AuthHeaders = {Authorization:string;"X-Tenant-ID":string};

export function authHeaders(): AuthHeaders | null {
  const token=sessionStorage.getItem("nomos_session");
  const tenant=sessionStorage.getItem("nomos_tenant");
  return token&&tenant?{Authorization:`Bearer ${token}`,"X-Tenant-ID":tenant}:null;
}

export function newIdempotencyKey(kind:string):string {
  const id=typeof crypto.randomUUID==="function"?crypto.randomUUID():Array.from(crypto.getRandomValues(new Uint8Array(16)),b=>b.toString(16).padStart(2,"0")).join("");
  return `web-${kind.toLowerCase()}-${id}`;
}

export async function apiError(response:Response):Promise<string>{
  if(response.status===401)return "เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่";
  if(response.status===403)return "คุณไม่มีสิทธิ์ทำรายการนี้";
  try{
    const body=await response.json() as {detail?:{code?:string;message?:string}};
    const code=body.detail?.code;
    if(code==="INSUFFICIENT_STOCK")return "สต็อกคงเหลือไม่เพียงพอ";
    if(code==="IDEMPOTENCY_CONFLICT")return "คำขอนี้ถูกส่งแล้วหรือข้อมูลเปลี่ยน กรุณาตรวจสอบรายการเคลื่อนไหวก่อนลองใหม่";
    if(code==="INVALID_DOCUMENT_STATE")return body.detail?.message??"สถานะข้อมูลไม่อนุญาตให้ทำรายการ";
  }catch{}
  return "ดำเนินการไม่สำเร็จ กรุณาลองใหม่";
}
