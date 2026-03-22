<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
import { onMounted } from 'vue'

const userStore = useUserStore()

onMounted(() => {
  // 检查本地存储的token
  const token = localStorage.getItem('token')
  if (token) {
    userStore.setToken(token)
    const userData = JSON.parse(localStorage.getItem('user') || '{}')
    userStore.setUser(userData)
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

body {
  background-color: #f5f7fa;
}
</style>