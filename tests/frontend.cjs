// DOM-stub logic tests: browser layout is not covered.
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
let logged=false;const nodes=new Map(),events={},requests=[];
function node(k){if(!nodes.has(k)){const classes=new Set();const n={value:'',innerHTML:'',textContent:'',style:{},dataset:{},classList:{add:x=>classes.add(x),remove:x=>classes.delete(x),toggle(x,on){on??=!classes.has(x);on?classes.add(x):classes.delete(x)},contains:x=>classes.has(x)},addEventListener(){},showModal(){this.open=true},close(){this.open=false},focus(){},reportValidity:()=>true,reset(){},querySelector:s=>node(s)};n.elements=new Proxy({},{get:(t,p)=>node('element:'+p)});nodes.set(k,n)}return nodes.get(k)}
for(const id of ['paymentPanel','otpForm','orderSuccess'])node('#'+id).classList.add('hidden');
const ps=[{id:'1',name:'Front Open Jabla',category:'Jablas',description:'Test',image:'/static/images/product-0.png',price:349,sale:279,stock:23,sizes:['0–3 months','3–6 months','6–9 months','9–12 months'].map((size,i)=>({size,stock:[12,3,0,8][i],availability:i===2?'Restock soon':'Available'}))},{id:'2',name:'Bath towel',category:'Bath & Sleep',description:'Test',image:'/static/images/product-1.png',price:599,sale:479,stock:8,sizes:[{size:'One size',stock:8,availability:'Available'}]}];
const memory=new Map(),storage={getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v)};
const sandbox={document:{hidden:false,querySelector:node,querySelectorAll:()=>[],addEventListener:(name,f)=>events[name]=f,referrer:''},localStorage:storage,sessionStorage:storage,crypto:{randomUUID:()=> '11111111-1111-1111-1111-111111111111'},window:{addEventListener(){},open(){throw Error('Checkout must not open WhatsApp')}},fetch:async(url,opt={})=>{requests.push({url,opt});if(url==='/api/auth/verify')logged=true;let data=url==='/api/products'?ps:url==='/api/account'?{customer:logged?{email:'test@example.com'}:null,csrf:'csrf'}:url==='/api/business'?{about:'Test brand'}:url==='/api/quote'?{subtotal:837,discount:0,login_discount:42,shipping:69,total:864}:url==='/api/auth/verify'?{customer:{email:'test@example.com'},csrf:'verified'}:url==='/api/orders'?{id:'private-uuid',number:'2610010001',payment_method:'credit_card',delivery:{available:true,earliest:'2026-10-04',latest:'2026-10-08',message:'Estimate'}}:{};return {ok:true,json:async()=>data}},setTimeout:()=>0,setInterval:()=>0,clearTimeout(){},console,Date,URLSearchParams,URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},location:{search:''},FormData:class{constructor(){this.data=Object.entries({name:'QA',phone:'9876543210',address:'Test',city:'Chennai',state:'Tamil Nadu',pin:'600001'})} [Symbol.iterator](){return this.data[Symbol.iterator]()}}};
const ctx=vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/store.js'),'utf8'),ctx);
(async()=>{
 await new Promise(setImmediate);
 assert(node('#products').innerHTML.includes('One Size'));
 assert(!/admin|low.stock|remaining|in stock/i.test(node('#products').innerHTML));
 events.change({target:{dataset:{size:'1'},value:'6–9 months'}});
 assert(node('#products').innerHTML.includes('Restock soon')&&node('#products').innerHTML.includes('Notify me'));
 vm.runInContext("add('1')",ctx);assert.equal(node('#count').textContent,0);
 events.change({target:{dataset:{size:'1'},value:'3–6 months'}});
 vm.runInContext("add('1');add('1');add('1');add('1')",ctx);assert.equal(node('#count').textContent,3);
 await vm.runInContext('beginCheckout()',ctx);assert(node('#loginDialog').open);
 // OTP continuation preserves cart and opens checkout.
 await node('#otpForm').onsubmit({preventDefault(){}});assert(node('#checkout').open);assert.equal(node('#count').textContent,3);
 node('#paymentMethod').value='credit_card';node('#cardName').value='QA';node('#cardNumber').value='4242424242424242';node('#cardExpiry').value='12/30';node('#cardCVV').value='123';node('#paymentOutcome').value='success';
 assert.doesNotThrow(()=>vm.runInContext('validatePayment()',ctx));
 node('#cardNumber').value='4111111111111111';assert.throws(()=>vm.runInContext('validatePayment()',ctx));node('#cardNumber').value='4242424242424242';
 node('#cardExpiry').value='01/20';assert.throws(()=>vm.runInContext('validatePayment()',ctx));node('#cardExpiry').value='12/30';
 node('#cardCVV').value='999';assert.throws(()=>vm.runInContext('validatePayment()',ctx));node('#cardCVV').value='123';
 node('#paymentMethod').value='upi';node('#upiId').value='personal@bank';assert.throws(()=>vm.runInContext('validatePayment()',ctx));node('#upiId').value='demo@tinytest';assert.doesNotThrow(()=>vm.runInContext('validatePayment()',ctx));
 node('#paymentMethod').value='net_banking';node('#testBank').value='';assert.throws(()=>vm.runInContext('validatePayment()',ctx));node('#testBank').value='demo-bank';assert.doesNotThrow(()=>vm.runInContext('validatePayment()',ctx));
 node('#paymentMethod').value='credit_card';node('#paymentPanel').classList.remove('hidden');
 await node('#checkoutForm').onsubmit({preventDefault(){},target:node('#checkoutForm')});
 assert(node('#orderSuccess').innerHTML.includes('2610010001'));
 assert(node('#orderSuccess').innerHTML.includes('2026-10-04'));
 assert(node('#orderSuccess').innerHTML.includes('No money was collected'));
 const order=JSON.parse(requests.find(r=>r.url==='/api/orders').opt.body);
 assert.deepEqual(order.payment,{method:'credit_card',outcome:'success'});
 assert(!/424242|cardCVV|123/.test(JSON.stringify(order.payment)));
 assert.equal(node('#count').textContent,0);
 console.log('PASS: One Size, sold-out Notify me, cart limits, mandatory OTP continuation, test-data validations, clean payment payload, readable confirmation, delivery dates and no WhatsApp redirect.');
})().catch(e=>{console.error(e);process.exitCode=1});
