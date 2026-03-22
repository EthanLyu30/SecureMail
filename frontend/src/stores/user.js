import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

  const isLoggedIn = computed(() => !!token.value)

  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }

  function setUser(userData) {
    user.value = userData
    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData))
    } else {
      localStorage.removeItem('user')
    }
  }

  async function login(username, password, domainId) {
    const res = await api.post('/auth/login', {
      username,
      password,
      domain_id: domainId
    })

    if (res.data.success) {
      setToken(res.data.data.token)
      setUser(res.data.data)
      return true
    }
    return false
  }

  async function register(username, password, domainId) {
    const res = await api.post('/auth/register', {
      username,
      password,
      domain_id: domainId
    })

    return res.data.success
  }

  function logout() {
    api.post('/auth/logout', { token: token.value })
    setToken('')
    setUser(null)
  }

  return {
    token,
    user,
    isLoggedIn,
    setToken,
    setUser,
    login,
    register,
    logout
  }
})