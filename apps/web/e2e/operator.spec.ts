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
