import { createApp } from 'vue';
import './style.css';
import App from './App.vue';
import router from './router';
import { installI18n } from './i18n';

const app = createApp(App);
installI18n(app);
app.use(router).mount('#app');
