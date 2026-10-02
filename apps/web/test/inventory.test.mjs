import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const routes=["inventory","inventory/stock","inventory/movements","inventory/receive","inventory/issue","inventory/transfer","inventory/adjust"];

test("phase 5 inventory routes are present",async()=>{
 for(const route of routes){const source=await readFile(new URL(`../src/app/${route}/page.tsx`,import.meta.url),"utf8");assert.ok(source.length>20,`missing ${route}`)}
});

test("inventory reads use authenticated tenant context",async()=>{
 for(const route of ["inventory","inventory/stock","inventory/movements"]){const source=await readFile(new URL(`../src/app/${route}/page.tsx`,import.meta.url),"utf8");assert.match(source,/authHeaders/)}
 const client=await readFile(new URL("../src/app/inventory/client.ts",import.meta.url),"utf8");
 assert.match(client,/Authorization/);assert.match(client,/X-Tenant-ID/);assert.match(client,/403/);
});

test("posting form calls phase 4 API with retry-safe idempotency",async()=>{
 const source=await readFile(new URL("../src/app/inventory/post-form.tsx",import.meta.url),"utf8");
 for(const term of ["/api/v1/inventory/transactions","Idempotency-Key","retryKey","Retry safely","INSUFFICIENT_STOCK","source_type","WEB_MANUAL"]){
   const haystack=term==="INSUFFICIENT_STOCK"?await readFile(new URL("../src/app/inventory/client.ts",import.meta.url),"utf8"):source;
   assert.ok(haystack.includes(term),`missing ${term}`);
 }
});

test("posting workflow derives organization and base unit from server master data",async()=>{
 const source=await readFile(new URL("../src/app/inventory/post-form.tsx",import.meta.url),"utf8");
 for(const term of ["base_unit_id","legal_entity_id","branch_id","warehouse_id"]){assert.ok(source.includes(term),`missing ${term}`)}
 assert.doesNotMatch(source,/on_hand\s*[+\-]=/);
});

test("phase 5 exposes loading empty permission insufficient-stock and retry states",async()=>{
 const client=await readFile(new URL("../src/app/inventory/client.ts",import.meta.url),"utf8");
 const stock=await readFile(new URL("../src/app/inventory/stock/page.tsx",import.meta.url),"utf8");
 const form=await readFile(new URL("../src/app/inventory/post-form.tsx",import.meta.url),"utf8");
 assert.match(stock,/Loading stock/);assert.match(stock,/No stock balances found/);
 assert.match(client,/ไม่มีสิทธิ์/);assert.match(client,/สต็อกคงเหลือไม่เพียงพอ/);
 assert.match(form,/Retry uses the same Idempotency-Key/);
});
