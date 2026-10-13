const fs = require('fs');
const { chromium } = require('C:/Users/Lion/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({headless:true, executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  try {
    const page = await browser.newPage({viewport:{width:1024,height:1100}});
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.evaluate(()=>window.openai={setWidgetState:async s=>{window.__lastState=s;}});
    await page.setContent(fs.readFileSync('F:/repo/arcs/work/basic-search-window.html','utf8'));
    const first=page.locator('.window').first();
    if(await first.locator('tbody tr').count()!==6)throw Error('Initial results missing');
    await first.locator('[data-field=type]').selectOption('arc');
    await first.locator('[data-do=search]').click();
    if(await first.locator('tbody tr').count()!==3)throw Error('Type search failed');
    await first.locator('[data-do=select-all]').check();
    await first.locator('[data-do=name]').click();
    const names=first.locator('[data-bind]');
    for(let i=0;i<3;i++)await names.nth(i).fill(String.fromCharCode(97+i));
    await first.locator('[data-do=bind]').click();
    if(!await first.locator('tbody').innerText().then(t=>t.includes('session: a')))throw Error('Binding failed');
    if(await page.locator('[data-do=pull]').count())throw Error('Direct Welder action remains');
    await first.locator('[data-do=copy-objects]').click();
    const copied=await page.evaluate(()=>JSON.parse(window.__lastState.privateContent.clipboard.text));
    if(!Array.isArray(copied)||copied.length!==3||copied.some(x=>typeof x!=='string'))throw Error('UUID-list format failed');
    await first.locator('[data-do=copy-search]').click();
    await page.locator('#bs-add').click();
    const second=page.locator('.window').nth(1);
    if(await second.locator('tbody tr').count()!==6)throw Error('Windows share results');
    await second.locator('[data-do=reset-clip]').click();
    await second.locator('[data-do=search]').click();
    if(await second.locator('tbody tr').count()!==3)throw Error('Clipboard reset failed');
    await second.locator('[data-field=title]').fill('coast');
    await second.locator('[data-do=search]').click();
    if(await second.locator('tbody tr').count()!==2)throw Error('Title substring failed');
    if(await first.locator('tbody tr').count()!==3)throw Error('Search result isolation failed');
    for(const width of [1024,736,360,320]) {
      await page.setViewportSize({width,height:1500});
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
      if(overflow)throw Error('Horizontal overflow at '+width);
    }
    if(errors.length)throw Error(errors.join('\n'));
    console.log('Verified filters, multi-selection, session naming, clipboard reset, independent windows, and responsive widths.');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
