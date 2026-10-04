const {chromium}=require('playwright-core');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});try{
const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:8766');await page.locator('#connection').filter({hasText:'CONNECTED'}).waitFor();
for(const [cohort,count] of [['single',200],['multi',50],['benign',50]]){await page.locator('#evaluation-cohort').selectOption(cohort);if(await page.locator('#evaluation-trials tr').count()!==count)throw Error('Wrong trial count '+cohort);if(!(await page.locator('#evaluation-metrics').textContent()).includes('/'))throw Error('Missing denominators');}
await page.locator('#evaluation-cohort').selectOption('single');
if(await page.locator('#evaluation-exposure progress').count()!==5)throw Error('Missing stage exposure');
await page.locator('#model-evaluation').screenshot({path:'docs/assets/model-evaluation-ui.png'});
await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:'docs/assets/workspace.png'});
await page.setViewportSize({width:390,height:844});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');
if(errors.length)throw Error(errors.join('\n'));console.log('Model evaluation: all cohorts, denominators, stage exposure, screenshots and mobile layout passed');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
