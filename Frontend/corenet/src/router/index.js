import Vue from 'vue'
import Router from 'vue-router'
import Events from '@/components/Events'
import Executions from '@/components/Executions'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/events',
      alias: ['/'],
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
