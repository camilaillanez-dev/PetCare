const CACHE_NAME='petcare-shell-v4';
const APP_SHELL=['/','/index.html','/landing.css','/landing.js','/ai-cat.css','/ai-cat.js','/theme.js','/portal.html','/portal.css','/portal.js','/clinic.html','/styles.css','/app.js','/manifest.webmanifest','/icons/petcare.svg','/icons/petcare-180.png','/icons/petcare-192.png','/icons/petcare-512.png'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(APP_SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE_NAME).map(key=>caches.delete(key)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  const request=event.request,url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
  if(request.mode==='navigate'){
    event.respondWith(fetch(request).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(request,copy))}return response}).catch(async()=>await caches.match(request,{ignoreSearch:true})||await caches.match('/portal.html')||Response.error()));
    return;
  }
  event.respondWith(caches.match(request,{ignoreSearch:true}).then(cached=>cached||fetch(request).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(request,response.clone()))}return response})));
});
