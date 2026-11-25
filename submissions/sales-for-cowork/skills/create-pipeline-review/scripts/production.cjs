const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const self=crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex');
module.exports=function(deck,plan,manifest=[]){
 const fail=m=>{throw Error(m)},hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
 if(!deck||typeof deck.writeFile!=='function')fail('writeFile required');
 for(const k of ['colors','fonts']){const t=plan.tokens?.[k];if(!t||typeof t!=='object'||Array.isArray(t)||!Object.keys(t).length||Object.values(t).some(v=>typeof v!=='string'||!v.trim()))fail('Missing tokens: '+k)}
 const ex=(plan.exemptions||[]).map(e=>({...e})),slots=plan.slots,assets=new Map();
 if(!Array.isArray(slots)||!Array.isArray(ex)||!Array.isArray(manifest))fail('Arrays required');
 for(const e of ex)if(!['image','icon'].includes(e.type)||!['user','host'].includes(e.authority)||typeof e.reason!=='string'||!e.reason.trim())fail('Invalid exemption');
 for(const s of slots){
  if(!s.id||typeof s.id!=='string'||!s.role?.trim()||!['image','icon'].includes(s.type)||assets.has(s.id))fail('Invalid slot');
  assets.set(s.id,{id:s.id,type:s.type,role:s.role,placements:0});
 }
 for(const t of ['image','icon'])if(!slots.some(s=>s.type===t)&&!ex.some(e=>e.type===t))fail('Missing role: '+t);
 for(const m of manifest){
  const a=assets.get(m.id);if(!a||a.path||m.success!==true||typeof m.path!=='string'||!path.isAbsolute(m.path))fail('Invalid manifest slot');
  const p=path.resolve(m.path),st=fs.statSync(p);if(!st.isFile()||!st.size)fail('Empty/nonfile asset');
  Object.assign(a,{path:p,sha256:hash(p)});
 }
 for(const a of assets.values())if(!a.path)fail('Missing successful file: '+a.id);
 function unchanged(a){if(hash(a.path)!==a.sha256)fail('Asset changed: '+a.id)}
 function place(id,slide,box){
  const a=assets.get(id);if(!a||typeof slide?.addImage!=='function')fail('Unknown slot/slide');
  const {x,y,w,h}=box||{};if(![x,y,w,h].every(Number.isFinite)||x<0||y<0||w<=0||h<=0)fail('Invalid box');
  unchanged(a);slide.addImage({path:a.path,x,y,w,h});a.placements++;
 }
 function seal(){
  for(const a of assets.values()){unchanged(a);if(!a.placements)fail('Unplaced: '+a.id)}
  return {guardSha256:self,status:ex.length?'exempted':'placement-recorded',assets:[...assets.values()].map(a=>({...a})),exemptions:ex.map(e=>({...e}))};
 }
 const write=deck.writeFile.bind(deck);deck.writeFile=(...args)=>{seal();return write(...args)};
 return {place,seal};
};
