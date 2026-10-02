import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const pages = [
  ["products", "Products"],
  ["categories", "Categories"],
  ["units", "Units"],
  ["warehouses", "Warehouses"],
  ["locations", "Locations"],
];

test("phase 3 master data routes are present", async () => {
  for (const [route, title] of pages) {
    const source = await readFile(new URL(`../src/app/${route}/page.tsx`, import.meta.url), "utf8");
    assert.match(source, new RegExp(title));
    assert.match(source, /X-Tenant-ID/);
    assert.match(source, /Authorization/);
  }
});

test("product web flow exposes search filter sort and pagination", async () => {
  const source = await readFile(new URL("../src/app/products/page.tsx", import.meta.url), "utf8");
  for (const term of ["search", "status", "sort", "cursor", "next_cursor"]) {
    assert.ok(source.includes(term), `missing ${term}`);
  }
});
