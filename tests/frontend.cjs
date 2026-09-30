// Headless DOM-stub checks; does not verify browser layout.
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const nodes=new Map();
function node(k){if(!nodes.has(k))nodes.set(k,{value:'',innerHTML:'',textContent:'',style:{},dataset:{},classList:{add(){},remove(){},toggle(){}},showModal(){this.open=true},close(){this.open=false}});return nodes.get(k)}
const sample={id:'1',name:'Front Open Jabla',category:'Jablas',description:'Cotton',image:'/static/images/product-0.png',price:349,sale:279,stock:23,sizes:['0–3 months','3–6 months','6–9 months','9–12 months'].map((size,i)=>({size,stock:[12,3,0,8][i],availability:i===2?'Restock soon':'Available'}))};
const memory=new Map();const storage={getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v)};
const events={};const sandbox={document:{querySelector:node,querySelectorAll:()=>[],addEventListener:(name,f)=>events[name]=f,referrer:''},localStorage:storage,sessionStorage:storage,crypto:{randomUUID:()=> '11111111-1111-1111-1111-111111111111'},window:{addEventListener(){},open(){}},fetch:async()=>({ok:true,json:async()=>[sample]}),setTimeout:()=>{},clearTimeout(){},console};
const context=vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/store.js'),'utf8'),context);
(async()=>{
 await new Promise(setImmediate);
 assert(node('#products').innerHTML.includes('Choose a size'));
 for(const [size,status] of [['3–6 months','Available'],['6–9 months','Restock soon']]){
  events.change({target:{dataset:{size:'1'},value:size}});
  const html=node('#products').innerHTML;
  assert(html.includes(`<div class="stock">${status}</div>`));
  assert(!/low.stock|admin|remaining|in stock/i.test(html));
  assert(html.includes('data-add="1" class="secondary" '+(status==='Restock soon'?'disabled':'')));
 }
 vm.runInContext("add('1')",context);assert.equal(node('#count').textContent,0);
 events.change({target:{dataset:{size:'1'},value:'3–6 months'}});
 vm.runInContext("add('1');add('1');add('1');add('1')",context);
 assert.equal(node('#count').textContent,3);
 const cart=JSON.parse(vm.runInContext('JSON.stringify(items())',context));
 assert.deepEqual(cart,[{id:'1',size:'3–6 months',qty:3}]);
 vm.runInContext('detail(products[0])',context);
 assert(node('#detailBody').innerHTML.includes('3–6 months'));
 assert(!/admin|low.stock|remaining/.test(node('#detailBody').innerHTML));
 console.log('PASS: customer labels, required size, sold-out button, per-size cart limits and size persistence; no admin alert text.');
})().catch(e=>{console.error(e);process.exitCode=1});
