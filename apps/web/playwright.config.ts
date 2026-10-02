import {defineConfig,devices} from "@playwright/test";
export default defineConfig({
 testDir:"./e2e",fullyParallel:false,retries:0,workers:1,reporter:"line",
 use:{baseURL:process.env.NOMOS_ORIGIN??"http://10.10.110.73",trace:"retain-on-failure",screenshot:"only-on-failure"},
 projects:[{name:"chromium",use:{...devices["Desktop Chrome"]}}],
});
