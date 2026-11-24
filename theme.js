(()=>{
 const root=document.documentElement;
 let theme='light';
 try{theme=localStorage.getItem('petcare-theme')||'light'}catch{}
 root.dataset.theme=theme;
 const paint=()=>document.querySelectorAll('[data-theme-toggle]').forEach(button=>{
   const dark=root.dataset.theme==='dark';
   button.innerHTML=dark?'☀ <span>Claro</span>':'☾ <span>Oscuro</span>';
   button.setAttribute('aria-label',dark?'Cambiar a tema claro':'Cambiar a tema oscuro');
   button.setAttribute('aria-pressed',String(dark));
   button.title=dark?'Cambiar a tema claro':'Cambiar a tema oscuro';
 });
 document.addEventListener('DOMContentLoaded',()=>{
   paint();
   document.querySelectorAll('[data-theme-toggle]').forEach(button=>button.addEventListener('click',()=>{
     root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';
     try{localStorage.setItem('petcare-theme',root.dataset.theme)}catch{}
     paint();
   }));
 });
})();
