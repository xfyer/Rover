function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
        .then(function(registration) {
          console.log('Registration Successful, Scope Is:', registration.scope);
        })
        .catch(function(error) {
          console.log('Service Worker Registration Failed, Error:', error);
        });
  }
}

registerServiceWorker();