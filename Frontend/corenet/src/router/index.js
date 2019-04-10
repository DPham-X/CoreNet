import Vue from 'vue'
import Router from 'vue-router'
import Events from '@/components/Events'
import Executions from '@/components/Executions'
import Home from '@/components/Home'
Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      alias: ['/home'],
      name: 'Home',
      component: Home
    },
    {
      path: '/events',
      name: 'Events',
      component: Events
    },
    {
      path: '/executions',
      name: 'Executions',
      component: Executions
    }
  ]
})
