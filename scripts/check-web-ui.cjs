/* Browser smoke check. --run-investigation invokes the real existing sandbox. */
const {chromium} = require('playwright-core');
const fs = require('node:fs/promises');
const path = require('node:path');
(async()=>{
  const browser=await chromium.launch({headless:true, executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const output=path.resolve(__dirname,'../artifacts/web/screenshots');await fs.mkdir(output,{recursive:true});
  try{
    await page.goto('http://127.0.0.1:8766');
    await page.locator('#connection').filter({hasText:'CONNECTED'}).waitFor();
    for(const name of ['components','end-to-end','investigation','deployment']){
      await page.locator(`[data-diagram="${name}"]`).click();
      await page.waitForFunction(()=>{const image=document.getElementById('diagram');return image.complete&&image.naturalWidth>0;});
    }
    await page.locator('[data-diagram="components"]').click();
    if(process.argv.includes('--run-investigation')||process.argv.includes('--run-full')){
      const action=process.argv.includes('--run-full')?'full':'investigate';
      await page.locator(`[data-action="${action}"]`).click();
      await page.waitForFunction(()=>document.getElementById('job-state').textContent==='RUNNING',null,{timeout:10000});
      await page.waitForFunction(()=>document.getElementById('job-state').textContent==='COMPLETE'||document.getElementById('job-state').textContent==='FAILED',null,{timeout:900000});
      const status=await page.locator('#job-state').textContent();
      if(status!=='COMPLETE')throw Error(await page.locator('#job-error').textContent());
      if(await page.locator('#verification-state').textContent()!=='GATE PASSED')throw Error('Verification gate did not pass');
      console.log(`Real ${action} workflow completed through browser controls`);
    }
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile page overflows horizontally');
    if(errors.length)throw Error(errors.join('\n'));
    console.log('Desktop/mobile rendering, all diagram controls and console checks passed');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
