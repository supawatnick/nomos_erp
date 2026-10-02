import {test,expect} from "@playwright/test";
const tenant="11111111-1111-4111-8111-111111111111";
const email="admin@demo.nomos.local";

test("demo operator can sign in and navigate critical ERP workspaces",async({page})=>{
 const failed:string[]=[];page.on("response",r=>{if(r.url().includes("/api/")&&r.status()>=400)failed.push(r.status()+" "+r.url())});
 await page.goto("/login");
 await expect(page.getByRole("heading",{name:"Operations workspace"})).toBeVisible();
 await expect(page.getByLabel("Tenant ID")).toHaveValue(tenant);
 await expect(page.getByLabel("Email")).toHaveValue(email);
 await page.getByRole("button",{name:"Sign in to NOMOS"}).click();
 await expect(page).toHaveURL(/\/$/);
 await expect(page.getByRole("heading",{name:"ERP workspace"})).toBeVisible();
 await expect(page.getByText("Active",{exact:true})).toBeVisible();
 for(const [label,path,heading] of [
  ["Inventory","/inventory","Inventory Control"],["Procurement","/procurement","Procurement"],
  ["Sales & CRM","/sales","Sales operations"],["Finance","/finance","Financial operations"],
  ["Approvals","/approvals","Approval Inbox"],["Reports","/reports","Operational Reports"],
 ]){
  await page.goto(path);await expect(page.getByRole("heading",{name:heading})).toBeVisible();
  await page.waitForTimeout(500); const alert=page.locator('.state.error, p.error[role="alert"]'); if(await alert.count()) throw new Error(path+': '+await alert.first().innerText()+' API='+failed.join(','));
 }
});

test("session persists across refresh and finance tabs are browser-operable",async({page})=>{
 await page.goto("/login");await page.getByRole("button",{name:"Sign in to NOMOS"}).click();await expect(page).toHaveURL(/\/$/);
 await page.reload(); await expect(page.getByRole('heading',{name:'ERP workspace'})).toBeVisible(); const stored=await page.evaluate(()=>({session:sessionStorage.getItem('nomos_session'),tenant:sessionStorage.getItem('nomos_tenant')})); expect(stored.session).toBeTruthy(); expect(stored.tenant).toBe(tenant); await expect(page.getByText('Active',{exact:true})).toBeVisible({timeout:10000});
 await page.goto("/finance");
 for(const name of ["Fiscal Periods","Journals / GL","AR / AP Invoices","Receipts / Payments","Chart of Accounts"]){
  await page.getByRole("button",{name}).click(); await page.waitForTimeout(250); const alert=page.locator('.state.error, p.error[role="alert"]'); if(await alert.count()) throw new Error('finance '+name+': '+await alert.first().innerText());
 }
});

test("inventory operational navigation renders without client errors",async({page})=>{
 const errors:string[]=[];page.on("pageerror",e=>errors.push(e.message));
 await page.goto("/login");await page.getByRole("button",{name:"Sign in to NOMOS"}).click();await expect(page).toHaveURL(/\/$/);
 await page.goto("/inventory");
 for(const name of ["Stock","Movements","Receive","Issue","Transfer","Adjust","Operations","Counts","Reorder","Reports"]){
  const link=page.getByRole("link",{name,exact:true}).first();await expect(link).toBeVisible();
 }
 expect(errors).toEqual([]);
});


test("inventory receive commits through browser and explicit reversal restores ledger state",async({page})=>{
 const failed:string[]=[];page.on("response",r=>{if(r.url().includes("/api/")&&r.status()>=400)failed.push(r.status()+" "+r.url())});
 await page.goto("/login");await page.getByRole("button",{name:"Sign in to NOMOS"}).click();await expect(page).toHaveURL(/\/$/);
 const ref="E2E-RECEIVE-"+Date.now();
 await page.goto("/inventory/receive");
 await expect(page.getByRole("heading",{name:"Receive Stock"})).toBeVisible();
 await page.getByLabel("Product").selectOption({index:1});
 await page.getByLabel("Source Location").selectOption({index:1});
 await page.getByLabel("Quantity").fill("1"); await expect(page.getByText("DEMO-WH",{exact:true})).toBeVisible();
 await page.getByLabel("Reference").fill(ref);
 await page.getByLabel("Reason").fill("Automated browser acceptance; reversed in same test");
 const submit=page.getByRole("button",{name:"Post RECEIVE"}); await expect(submit).toBeEnabled(); await submit.click(); await page.waitForTimeout(250); const immediateError=page.locator(".state.error"); if(await immediateError.count()) throw new Error("receive preflight: "+await immediateError.innerText()); await page.waitForRequest(r=>r.url().includes("/api/v1/inventory/transactions")&&r.method()==="POST",{timeout:3000});
 const posted=page.getByRole("status"); try{await expect(posted).toContainText("POSTED")}catch{const err=page.locator(".state.error");throw new Error("receive failed: "+(await err.count()?await err.innerText():"no UI error")+" API="+failed.join(",")+" disabled="+await submit.isDisabled()+" text="+await submit.innerText())}
 await page.goto("/inventory/movements");
 const row=page.getByRole("row").filter({hasText:ref});
 await expect(row).toBeVisible();
 await expect(row.getByText("RECEIVE",{exact:true})).toBeVisible();
 page.once("dialog",d=>d.accept("Automated E2E cleanup reversal"));
 await row.getByRole("button",{name:"Reverse"}).click();
 await expect(page.getByRole("status")).toContainText("Reversal posted");
 await expect(page.getByRole("row").filter({hasText:"REVERSAL"}).first()).toBeVisible();
 await expect(page.locator(".state.error")).toHaveCount(0);
});
