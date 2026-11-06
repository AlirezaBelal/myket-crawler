import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
const out='qa-evidence'; await mkdir(out,{recursive:true});
const browser=await chromium.launch();
const results=[];
const sites=[['product',process.env.PRODUCT_URL||'http://127.0.0.1:8765/'],['portfolio','https://alirezabelal.github.io/work/lab/myket-crawler/']];
try {
for(const [name,url] of sites) for(const width of [320,375,390,768,1024,1440,1920]){
 const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
 const page=await context.newPage();
 const errors=[],requests=[],bad=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 page.on('request',r=>requests.push(r.url()));
 page.on('response',r=>{if(r.status()>=400)bad.push([r.status(),r.url()]);});
 await page.goto(url,{waitUntil:'networkidle'}); await page.evaluate(()=>document.fonts.ready);
 assert.equal(await page.locator('h1').count(),1);
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'horizontal overflow '+name+' '+width);
 assert(await page.locator('img').evaluateAll(xs=>xs.every(x=>x.complete&&x.naturalWidth>0)),'broken image');
 for(const a of await page.locator('a[href^="#"]').all()){const href=await a.getAttribute('href');if(href!=='#')assert(await page.locator(href).count(),'missing anchor '+href);}
 const expected=name==='product'?'https://github.com/AlirezaBelal/myket-crawler':'https://alirezabelal.github.io/myket-crawler/';
 assert(await page.locator('a[href="'+expected+'"]').count(),'CTA destination');
 await page.keyboard.press('Tab');
 assert(await page.evaluate(()=>{const e=document.activeElement;const c=getComputedStyle(e);return e!==document.body&&(c.outlineStyle!=='none'||c.boxShadow!=='none');}),'visible keyboard focus');
 for(const summary of await page.locator('summary').all()){await summary.focus();await page.keyboard.press('Enter');}
 const accessibility=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
 await writeFile(out+'/'+name+'-'+width+'-accessibility.json',JSON.stringify(accessibility,null,2));
 assert.deepEqual(accessibility.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],'accessibility violations');
 if(name==='product') assert(await page.locator('h1').evaluate(e=>parseFloat(getComputedStyle(e).fontSize)<=60),'compact hero scale');
 const external=requests.filter(u=>/^https?:/.test(u)&&new URL(u).origin!==new URL(url).origin);
 assert.equal(external.length,0,'unexpected external request '+external.join(','));
 assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);
 await page.screenshot({path:out+'/'+name+'-'+width+'.png',fullPage:true});
 results.push({name,width,url,errors,external,assets:'passed',overflow:'passed',keyboard:'passed',h1:await page.locator('h1').evaluate(e=>getComputedStyle(e).fontSize)});
 await context.close();
}
} finally {await writeFile(out+'/results.json',JSON.stringify(results,null,2));await browser.close();}
