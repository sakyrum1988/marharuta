/* Execute the rendered calculators against a minimal DOM and controlled API. */
const assert = require('node:assert/strict');
const vm = require('node:vm');
const input = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
const tick = () => new Promise(resolve => setImmediate(resolve));

function environment(lang, fetch) {
  const elements = new Map();
  const values = {'cc-country':'thailand', 'cc-accom':'budget', 'cc-food':'local',
    'cc-transport':'public','cc-lifestyle':'minimal','cc-people':'1','cc-cur-select':'THB',
    'bp-country-sel':'thailand','bp-emergency':'3'};
  const document = {
    documentElement: {lang}, readyState:'complete',
    getElementById(id) {
      if (!elements.has(id)) {
        const classes = new Set();
        elements.set(id, {value:values[id] || '0', textContent:'',innerHTML:'',style:{}, handlers:{},
          classList:{add:c=>classes.add(c),remove:c=>classes.delete(c),contains:c=>classes.has(c)},
          addEventListener(type, fn){this.handlers[type]=fn;}, scrollIntoView(){}});
      }
      return elements.get(id);
    },
    addEventListener(){}, querySelectorAll(){return [];}
  };
  const ctx = vm.createContext({document, fetch, Date, URLSearchParams, AbortController,
    setTimeout:(fn,ms)=>{const t=setTimeout(fn,ms);t.unref();return t;}, clearTimeout, console});
  ctx.window = ctx;
  vm.runInContext(input.shared, ctx);
  return {ctx, get:id=>document.getElementById(id)};
}

(async () => {
  for (const entry of input.pages) {
    for (const mode of ['success','network-error','invalid','stale','missing-currency']) {
      let resolveFetch, rejectFetch;
      const pending = new Promise((resolve,reject)=>{resolveFetch=resolve;rejectFetch=reject;});
      const {ctx,get} = environment(entry.lang,()=>pending);
      vm.runInContext(entry.script,ctx);
      const cost = entry.path.includes('cost-calculator');
      if (cost) {
        get('cc-btn').handlers.click();
        assert.equal(get('cc-br-rent').textContent,'$250 USD');
        assert.equal(get('cc-total-month').textContent,'$650 USD');
      } else {
        get('bp-autofill-btn').handlers.click();
        get('bp-calc-btn').handlers.click();
        assert.equal(get('bp-grand-local').textContent,'');
        assert.ok(!get('bp-rate-info').innerHTML.includes('(live)'));
      }
      if (mode === 'network-error') rejectFetch(new Error('offline'));
      else {
        const now = Math.floor(Date.now()/1000);
        const body = mode === 'invalid' ? {result:'error',rates:{USD:1,THB:-1}} : {
          result:'success',base_code:'USD', rates:{USD:1,EUR:.9,...(mode==='missing-currency'?{}:{THB:30})},
          time_last_update_unix:mode==='stale'?now-5*86400:now
        };
        resolveFetch({ok:true,json:async()=>body});
      }
      await tick(); await tick();
      if (mode==='success') {
        if(cost) assert.equal(get('cc-total-month').textContent.replace(/\D/g,''),'19500');
        else assert.ok(get('bp-grand-local').textContent.includes('THB'));
      } else {
        if(cost) assert.equal(get('cc-total-month').textContent,'$650 USD');
        else assert.equal(get('bp-grand-local').textContent,'');
      }
      console.log(entry.path,mode,'OK');
    }
  }
  const {ctx} = environment('en', async()=>({ok:true,json:async()=>({daily:{time:['2026-01-01'],temperature_2m_mean:[null],precipitation_sum:[null]}})}));
  assert.equal(await ctx.RtaData.climate(13.75,100.52),null);
  assert.equal(ctx.RtaData.rate({THB:0},'THB'),null);
  assert.equal(ctx.RtaData.rate({THB:Infinity},'THB'),null);
  const timeout = environment('en', (url, options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(new Error('abort')))));
  timeout.ctx.setTimeout=(fn)=>setTimeout(fn,5);
  await assert.rejects(timeout.ctx.RtaData.json('/timeout'));
  console.log('Empty climate, invalid rates and request timeout OK');
})().catch(error=>{console.error(error);process.exitCode=1;});
