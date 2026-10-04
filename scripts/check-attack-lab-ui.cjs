const {chromium}=require('playwright-core');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  const p=await b.newPage({viewport:{width:1440,height:1100}}),errors=[];
  p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://127.0.0.1:8766');
  await p.locator('#connection').filter({hasText:'CONNECTED'}).waitFor();
  if(process.argv.includes('--run')){
   await p.locator('[data-action="attacks"]').click();
   await p.waitForFunction(()=>document.getElementById('job-state').textContent==='RUNNING');
   await p.waitForFunction(()=>['COMPLETE','FAILED'].includes(document.getElementById('job-state').textContent),null,{timeout:600000});
   if(await p.locator('#job-state').textContent()!=='COMPLETE')throw Error(await p.locator('#job-error').textContent());
  }
  for(const mode of ['unguarded','finguard','openshell','both']){
   await p.locator('#attack-mode').selectOption(mode);
   if(await p.locator('#attack-rows tr').count()!==18)throw Error('Missing case rows');
  }
  await p.locator('#attack-filter').selectOption('attacks');
  if(await p.locator('#attack-rows tr').count()!==14)throw Error('Attack filter failed');
  await p.locator('#attack-filter').selectOption('controls');
  if(await p.locator('#attack-rows tr').count()!==4)throw Error('Control filter failed');
  await p.locator('#attack-filter').selectOption('all');
  await p.locator('#attack-rows button').first().click();
  if(!(await p.locator('#attack-trace-json').textContent()).includes('wrong_transaction'))throw Error('Trace inspection failed');
  await p.locator('#attack-trace').evaluate(e=>e.open=false);
  await p.locator('#attack-lab').screenshot({path:'docs/assets/attack-lab.png'});
  await p.setViewportSize({width:390,height:844});
  if(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');
  if(errors.length)throw Error(errors.join('\n'));
  console.log('Attack Lab controls, 4 configurations, filters, trace viewer and mobile layout passed');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
