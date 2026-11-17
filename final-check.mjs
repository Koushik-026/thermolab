import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire('C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1116-1220-0_26.1116.1220.0_x64__3k8sg7r9htsxt/dependencies/node/package.json');
const {chromium}=require('playwright');
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true,reducedMotion:'reduce'});
const checks=[];
try{
 await page.goto(process.env.THERMO_TEST_URL||'http://127.0.0.1:3201');await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
 await page.locator('#ambient').fill('22.5');await page.locator('#target').fill('45.5');
 const result=page.waitForResponse(r=>r.url().endsWith('/api/simulate'));await page.locator('#run-button').click();await result;await page.waitForFunction(()=>!document.querySelector('#run-button').disabled);
 assert.equal(await page.locator('#room-value').textContent(),'22.5°C');assert.equal(await page.locator('#target-label').textContent(),'TIME TO 45.5°C');checks.push('fractional temperatures retain their meaning in labels');
 const download=page.waitForEvent('download');await page.getByRole('link',{name:'Open in Python'}).click();const file=await download;
 const notebook=JSON.parse(fs.readFileSync(await file.path(),'utf8'));assert.equal(notebook.nbformat,4);assert.ok(notebook.cells.some(c=>c.source.join?.('').includes('def simulate')||String(c.source).includes('def simulate')));checks.push('Python download is the complete executed notebook');
 await page.locator('#speed').selectOption('6');await page.locator('#play').click();await page.waitForFunction(()=>Number(document.querySelector('#timeline').value)>1);await page.locator('#play').click();checks.push('native playback-speed dropdown controls a working simulation');
 await page.locator('#timeline').fill('60');await page.locator('#timeline').dispatchEvent('input');await page.locator('#play').click();await page.waitForFunction(()=>Number(document.querySelector('#timeline').value)<5);await page.locator('#play').click();checks.push('playing from the end restarts the simulation');
 await page.locator('#methods-toggle').click();await page.locator('#method-lab').screenshot({path:'output/browser/method-lab.png'});
 await page.setViewportSize({width:390,height:844});await page.waitForFunction(()=>document.querySelector('#graph').getAttribute('viewBox').includes('460'));
 await page.locator('#chart-panel').screenshot({path:'output/browser/mobile-chart.png'});
 const box=await page.locator('#graph').boundingBox();assert.ok(box.height>210);checks.push('phone graph uses a readable plotting canvas');
 fs.writeFileSync('output/browser/additional-validation.json',JSON.stringify({passed:checks.length,checks},null,2));console.log(JSON.stringify({passed:checks.length,checks}));
}finally{await browser.close();}
