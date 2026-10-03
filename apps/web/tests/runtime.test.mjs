import test from "node:test";
import assert from "node:assert/strict";

const origin=process.env.NOMOS_ORIGIN??"http://127.0.0.1:3000";
const apiOrigin=process.env.NOMOS_API_ORIGIN??origin;
const tenant=process.env.NOMOS_DEMO_TENANT??"11111111-1111-4111-8111-111111111111";
const email=process.env.NOMOS_DEMO_EMAIL??"admin@demo.nomos.local";

async function html(path){
 const r=await fetch(origin+path);assert.equal(r.status,200,`${path} must return 200`);
 const body=await r.text();assert.match(body,/NOMOS/i,`${path} must render NOMOS shell`);return body;
}

test("critical ERP routes render through deployed Web",async()=>{
 for(const path of ["/","/login","/admin","/approvals","/categories","/crm","/finance","/imports","/inventory","/inventory/adjust","/inventory/counts","/inventory/imports","/inventory/issue","/inventory/movements","/inventory/operations","/inventory/receive","/inventory/reorder","/inventory/reports","/inventory/stock","/inventory/transfer","/locations","/partners","/procurement","/products","/reports","/sales","/settings/subscription","/units","/warehouses"]){await html(path)}
});

test("health and readiness are healthy through configured origin",async()=>{
 for(const path of ["/health","/ready"]){const r=await fetch(apiOrigin+path);assert.equal(r.status,200);const b=await r.json();assert.ok(["ok","ready"].includes(b.status))}
});

test("demo login creates a tenant session and resolves context",async()=>{
 const login=await fetch(apiOrigin+"/api/v1/auth/login",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({email,password:"",tenant_id:tenant})});
 assert.equal(login.status,200,"demo login must succeed");
 const payload=await login.json();assert.equal(payload.data.tenant_id,tenant);assert.ok(payload.data.session_token);assert.ok(payload.data.permissions.length>0);
 const headers={Authorization:`Bearer ${payload.data.session_token}`,"X-Tenant-ID":tenant};
 const context=await fetch(apiOrigin+"/api/v1/auth/context",{headers});assert.equal(context.status,200,"session context must resolve");
 const ctx=await context.json();assert.equal(ctx.data.tenant_id,tenant);assert.ok(ctx.data.permissions.length>0);
 for(const path of ["/api/v1/master-data/summary","/api/v1/organization","/api/v1/inventory/balances","/api/v1/procurement/requests","/api/v1/procurement/rfqs","/api/v1/procurement/orders","/api/v1/sales/quotations","/api/v1/sales/orders","/api/v1/finance/accounts","/api/v1/finance/periods","/api/v1/finance/journals","/api/v1/finance/invoices","/api/v1/finance/payments","/api/v1/approvals","/api/v1/reports"]){
  const r=await fetch(apiOrigin+path,{headers});assert.equal(r.status,200,`${path} must be readable by demo admin`);
 }
});
