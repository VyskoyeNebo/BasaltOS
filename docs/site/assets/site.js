document.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',async()=>{
  try{await navigator.clipboard.writeText(document.getElementById(button.dataset.copy).textContent.trim());button.textContent='已复制';setTimeout(()=>button.textContent='复制',1600)}catch{button.textContent='请选中复制'}
}));
const toggle=document.querySelector('.docs-toggle'), sidebar=document.querySelector('.sidebar');
toggle?.addEventListener('click',()=>{const open=sidebar.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));});
const search=document.querySelector('[data-search]'),results=document.querySelector('.search-results');
if(search&&results){let pending;search.addEventListener('input',async()=>{
  const query=search.value.trim().toLocaleLowerCase();results.replaceChildren();if(query.length<2)return;
  try{pending??=fetch(search.dataset.search).then(r=>{if(!r.ok)throw new Error('Search unavailable');return r.json()});const index=await pending;if(search.value.trim().toLocaleLowerCase()!==query)return;const score=p=>(p.title.toLocaleLowerCase().includes(query)?100:0)+(/\/(QUICKSTART|SECURITY|GAMING|PRIVACY|SECUREBOOT|PUBLISHING|RELEASE-NOTES-0.1.0)\.html$/.test(p.url)?30:0);index.filter(p=>(p.title+' '+p.text).toLocaleLowerCase().includes(query)).sort((a,b)=>score(b)-score(a)).slice(0,8).forEach(p=>{const a=document.createElement('a');a.href=p.url;a.textContent=p.title;results.append(a);});if(!results.children.length)results.textContent='没有找到相关文档。'}catch{pending=undefined;if(search.value.trim().toLocaleLowerCase()===query)results.textContent='搜索暂不可用，请使用下方目录。'}
});}
