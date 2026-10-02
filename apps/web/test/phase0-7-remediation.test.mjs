import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";

test("phase 0-7 remediation exposes administration surfaces",async()=>{const s=await readFile(new URL("../src/app/admin/page.tsx",import.meta.url),"utf8");assert.match(s,/\/api\/v1\/admin\/\$\{path\}/);assert.match(s,/Users, Roles & Audit/);assert.match(s,/Audit trail/)});
test("controlled import requires stage validate commit workflow",async()=>{const s=await readFile(new URL("../src/app/imports/page.tsx",import.meta.url),"utf8");assert.match(s,/\/api\/v1\/imports/);assert.match(s,/Validate/);assert.match(s,/Commit/);assert.match(s,/READY_TO_COMMIT/);assert.match(s,/side-effect free/)});
test("operations navigation exposes remediation workflows",async()=>{const s=await readFile(new URL("../src/app/page.tsx",import.meta.url),"utf8");assert.match(s,/href="\/admin"/);assert.match(s,/href="\/imports"/)});
