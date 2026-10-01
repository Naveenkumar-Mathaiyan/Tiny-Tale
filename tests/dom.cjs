// Real DOM behaviour via jsdom; this is not a visual-browser test.
// Optional development dependency: npm install --no-save jsdom
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');const root=path.join(__dirname,'../static');
const product={id:'1',name:'Jabla',category:'Jablas',description:'Soft cotton',image:'/static/images/product-0.png',price:349,sale:279,stock:8,active:true,sizes:[{size:'One size',stock:8,enabled:true,availability:'Available'}],gallery:[{url:'/assets/test',kind:'video',alt:'Preview'}],details:'Full details',material:'Cotton',care:'Gentle wash'};
function dom(name){const d=new JSDOM(fs.readFileSync(path.join(root,name),'utf8'),{url:'https://shop.example/',runScripts:'outside-only'});d.window.HTMLDialogElement.prototype.showModal=function(){this.open=true};d.window.HTMLDialogElement.prototype.close=function(){this.open=false};return d}
const pause=()=>new Promise(r=>setTimeout(r,20));
(async()=>{
 const d=dom('index.html'),w=d.window;let traffic=0;
 w.localStorage.setItem('tiny-consent','yes'); // Must not send v4 traffic under old permission.
 w.fetch=async(url,opt={})=>{let data={};if(url==='/api/products')data=[product];if(url==='/api/account')data={csrf:'test',customer:null,otp_ready:false};if(url==='/api/business')data={about:'Tiny Tale'};if(url==='/api/banners')data=[];if(url==='/api/traffic')traffic++;return {ok:true,json:async()=>data}};
 for(const file of ['store.js','store-v4.js'])vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),d.getInternalVMContext());await pause();
 assert.equal(traffic,0);assert.equal(w.document.querySelector('#accountButton').textContent,'Login / Register');
 assert(w.document.querySelector('#offerBanners').textContent.includes('extra 5%'));
 assert(w.document.querySelector('[data-favourite]'));
 w.document.querySelector('[data-favourite]').click();assert(w.localStorage.getItem('tiny-favourites').includes('1'));
 w.document.querySelector('[data-view]').click();assert(w.document.querySelector('#detail').open);assert(w.document.querySelector('#detail video'));assert(w.document.querySelector('#detail').textContent.includes('Full details'));
 w.document.querySelector('#accept').click();await pause();assert.equal(traffic,1);
 w.document.querySelector('#accountButton').click();await pause();assert(w.document.querySelector('#loginMessage').textContent.includes('temporarily unavailable'));
 d.window.close();
 const a=dom('admin.html'),aw=a.window;let saves=[];
 const journey={sessions:0,active_seconds:0,average_seconds:0,test_successes:0,funnel:[],reach:[],duration:[],errors:[],recent:[]};
 const analytics={sessions:0,enquiries:0,confirmed:0,revenue:0,products:[],searches:[],devices:[],events:[],browsers:[],systems:[],sources:[],low_stock:[]};
 aw.fetch=async(url,opt={})=>{if(opt.method==='POST')saves.push(url);const route=url.replace('/api/admin/','').split('?')[0];const data=({session:{csrf:'test'},analytics,products:[product],journey,'email-status':{status:{configured:false,message:'Missing',checked:'now'},instructions:'Set BREVO_API_KEY'},numbering:{prefix:'',date:true,padding:4,next:1,last:0},marketing:{sessions:0,daily:[],hours:[],countries:[],states:[],campaigns:[],sources:[],recent:[]},banners:[],'merch/1':{gallery:product.gallery,details:product.details,care:product.care,material:product.material}})[route]||{};return {ok:true,json:async()=>data}};
 for(const file of ['admin.js','admin-extra.js','admin-v4.js'])vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),a.getInternalVMContext());await pause();
 for(const tab of ['email','numbering','marketing','media','banners']){aw.document.querySelector(`[data-tab="${tab}"]`).click();await pause();assert.equal(aw.document.querySelector('#error').textContent,'',tab);assert(aw.document.querySelector('#content').textContent.length>20,tab);if(tab==='media'){assert(aw.document.querySelector('#galleryList video'));aw.document.querySelector('#merchForm').dispatchEvent(new aw.Event('submit',{cancelable:true}));await pause();assert(saves.includes('/api/admin/merch/1'))}if(tab==='banners'){aw.document.querySelector('#newBanner').click();assert(aw.document.querySelector('#bannerForm'))}}
 a.window.close();console.log('PASS DOM: complete script loading, fresh analytics consent, login status, favourites, product video/details, default banner; admin diagnostics, charts, media save, numbering and banner editor.');
})().catch(e=>{console.error(e);process.exit(1)});
