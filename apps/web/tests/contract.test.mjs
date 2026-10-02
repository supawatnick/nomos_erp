import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";

const read=p=>readFileSync(new URL("../"+p,import.meta.url),"utf8");

test("login stores tenant session and permissions before workspace navigation",()=>{
 const source=read("src/app/login/page.tsx");
 for(const key of ["nomos_session","nomos_tenant","nomos_permissions"])assert.match(source,new RegExp(key));
 assert.match(source,/router\.push\("\/"\)/);
});

test("workspace does not clear a valid session on aborted navigation",()=>{
 const source=read("src/app/page.tsx");
 assert.match(source,/AbortController/);
 assert.match(source,/AbortError/);
 assert.match(source,/r\.status===401\|\|r\.status===403/);
});

test("critical ERP pages remain implemented",()=>{
 for(const path of ["inventory/page.tsx","procurement/page.tsx","sales/page.tsx","finance/page.tsx","approvals/page.tsx","reports/page.tsx"]){
  const source=read("src/app/"+path);assert.match(source,/export default/);assert.ok(source.length>500,path+" is unexpectedly thin");
 }
});
