// 用真实浏览器验证静态路径、中文正文、主题菜单和跨页跳转。
import assert from 'node:assert/strict';
const {default:puppeteer}=await import(process.env.PUPPETEER_MODULE || 'puppeteer');
const base=process.argv[2];
const browser=await puppeteer.launch({headless:true,args:['--no-sandbox']});
try {
  const page=await browser.newPage();
  await page.setViewport({width:1440,height:1000});
  const errors=[], failed=[];
  page.on('pageerror',error=>errors.push(String(error)));
  page.on('response',response=>{
    if(response.url().startsWith(base)&&response.status()>=400)failed.push([response.status(),response.url()]);
  });
  for(const route of ['oss/python/deepagents/overview/','oss/python/langchain/overview/','oss/python/langgraph/overview/']){
    const response=await page.goto(base+route,{waitUntil:'networkidle2',timeout:60000});
    assert.equal(response.status(),200);
    const text=await page.$eval('main',n=>n.innerText);
    assert.match(text,/[\u4e00-\u9fff]/);
    assert(!text.includes('Application error:'));
    console.log('页面通过：'+route);
  }
  await page.goto(base+'oss/python/deepagents/overview/',{waitUntil:'networkidle2'});
  await page.click('[aria-label="Change theme preference"]');
  await page.waitForSelector('[role="menu"]',{visible:true});
  await page.keyboard.press('Escape');
  const next=await page.$('a[href*="/oss/python/deepagents/quickstart"]');
  assert(next,'找不到快速开始的导航链接');
  await Promise.all([page.waitForNavigation({waitUntil:'networkidle2',timeout:60000}),next.click()]);
  assert(page.url().startsWith(base+'oss/python/deepagents/quickstart'));
  const external=await page.$$eval('a[href]',nodes=>nodes.map(n=>n.href).filter(h=>h.startsWith('https://docs.langchain.com/')));
  assert(external.length>0,'范围外文档应链接到官方站');
  console.log('官方外链示例：'+external[0]);
  await page.setViewport({width:390,height:844});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'手机页面出现横向溢出');
  assert.deepEqual(errors,[]);
  assert.deepEqual(failed,[]);
  console.log('主题菜单、跨页跳转、手机布局及资源请求通过。');
}finally{await browser.close()}
