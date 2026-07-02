self.addEventListener('install', (e) => {
  console.log('[Service Worker] Installed');
});

self.addEventListener('fetch', (e) => {
  // Service worker is active but currently just a pass-through shell for PWA installation
});
