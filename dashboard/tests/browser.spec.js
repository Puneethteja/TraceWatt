import { test, expect } from '@playwright/test';

test('landing explains the concept, cause interaction works, and console opens',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.getByRole('heading',{name:/Find the cause/})).toBeVisible();
 await page.getByRole('tab',{name:/Meter Malfunction/}).click();
 await expect(page.getByRole('tabpanel')).toContainText('measurement problems');
 await page.screenshot({path:'test-results/landing-desktop.png',fullPage:true});
 await page.getByRole('link',{name:'Open Mission Console',exact:false}).first().click();
 await expect(page.getByRole('heading',{name:'A clearer view of your grid.'})).toBeVisible();
 await expect.poll(()=>errors).toEqual([]);
});
for(const [route,title] of [['consumers','Consumer explorer'],['cases','Case management'],['feeders','Feeder analytics'],['alerts','Alert center'],['consumption','Consumption data'],['baselines','Baseline library'],['pipeline','System pipeline'],['health','System health'],['simulation','A signal becomes a record.']]){
 test(route+' route renders against the real backend',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/console/'+route);await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();
  await expect(page.locator('.skeleton')).toHaveCount(0);
  await expect.poll(()=>errors).toEqual([]);
  if(route==='simulation'){await expect(page.getByRole('button',{name:'Start',exact:true})).toBeDisabled();await page.screenshot({path:'test-results/simulation-desktop.png',fullPage:true});}
 });
}
test('backend unavailable state is honest and retry is accessible',async({page})=>{
 await page.route(/http:\/\/127\.0\.0\.1:5173\/api\//,route=>route.abort('connectionfailed'));
 await page.goto('/console/health');
 await expect(page.getByText('Unable to connect to TraceWatt backend. Check the backend URL and connection.')).toBeVisible();
 await expect(page.getByRole('button',{name:'Retry',exact:true})).toBeVisible();
 await page.screenshot({path:'test-results/backend-unavailable.png'});
});
test('mobile navigation, focus and layout work without horizontal overflow',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/landing-mobile.png',fullPage:true});
 await page.goto('/console');await page.getByRole('button',{name:'Toggle navigation'}).click();
 await page.getByRole('link',{name:'Health',exact:false}).click();await expect(page.getByRole('heading',{name:'System health',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/console-mobile.png',fullPage:true});
});
test('health polling refreshes through the existing endpoint',async({page})=>{
 test.setTimeout(45000);
 let count=0;page.on('request',request=>{if(request.url().endsWith('/api/health'))count++;});
 await page.goto('/console/health');await expect(page.getByRole('heading',{name:'System health',exact:true})).toBeVisible();
 const before=count;await expect.poll(()=>count,{timeout:35000}).toBeGreaterThan(before);
});
test('existing backend rejects invalid ReadingIn with HTTP 422',async({request})=>{
 const response=await request.post('/api/readings',{data:{}});expect(response.status()).toBe(422);
});
