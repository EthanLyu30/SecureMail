import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Layout from '../views/Layout.vue'
import Inbox from '../views/mail/Inbox.vue'
import Sent from '../views/mail/Sent.vue'
import Drafts from '../views/mail/Drafts.vue'
import Compose from '../views/mail/Compose.vue'
import MailDetail from '../views/mail/MailDetail.vue'
import Groups from '../views/Groups.vue'
import Search from '../views/Search.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '',
        redirect: '/inbox'
      },
      {
        path: 'inbox',
        name: 'Inbox',
        component: Inbox
      },
      {
        path: 'sent',
        name: 'Sent',
        component: Sent
      },
      {
        path: 'drafts',
        name: 'Drafts',
        component: Drafts
      },
      {
        path: 'compose',
        name: 'Compose',
        component: Compose
      },
      {
        path: 'mail/:id',
        name: 'MailDetail',
        component: MailDetail
      },
      {
        path: 'groups',
        name: 'Groups',
        component: Groups
      },
      {
        path: 'search',
        name: 'Search',
        component: Search
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (!token && to.path !== '/login' && to.path !== '/register') {
    next('/login')
  } else if (token && (to.path === '/login' || to.path === '/register')) {
    next('/inbox')
  } else {
    next()
  }
})

export default router