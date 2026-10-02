import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";

for(const route of ["operations","counts","reorder","reports"]){
 test(`phase 6 route ${route} exists`,async()=>{const s=await readFile(new URL(`../src/app/inventory/${route}/page.tsx`,import.meta.url),"utf8");assert.ok(s.length>100)});
}
test("stock count posts variance with idempotency",async()=>{const s=await readFile(new URL("../src/app/inventory/counts/page.tsx",import.meta.url),"utf8");assert.match(s,/stock-counts/);assert.match(s,/Idempotency-Key/);assert.match(s,/Post variance/)});
test("reorder remains a signal and not procurement creation",async()=>{const s=await readFile(new URL("../src/app/inventory/reorder/page.tsx",import.meta.url),"utf8");assert.match(s,/does not create Purchase Orders/);assert.doesNotMatch(s,/purchase-orders/)});
test("operational report supports csv export",async()=>{const s=await readFile(new URL("../src/app/inventory/reports/page.tsx",import.meta.url),"utf8");assert.match(s,/reports\/summary/);assert.match(s,/text\/csv/);assert.match(s,/Export CSV/)});
