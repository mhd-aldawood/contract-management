import { createApp } from 'vue';
import App from './App.vue';
import router from './presentation/router';
import '@/assets/styles/main.css';
import { rootLogger } from '@/core/logger';

const app = createApp(App);                  // (1) create first

app.provide('$log', rootLogger);             // (2) Composition API access
app.config.globalProperties.$log = rootLogger; // (3) Options API access (optional)

app.config.errorHandler = (err, instance, info) => {
  rootLogger.error('Unhandled Vue error:', { err, info });
};

window.addEventListener('unhandledrejection', (event) => {
  rootLogger.error('Unhandled promise rejection:', event.reason);
});

app.use(router).mount('#app'); 
