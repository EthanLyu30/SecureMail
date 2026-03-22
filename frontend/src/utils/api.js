import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error.response?.data || error)
  }
)

// 认证API
export const login = (email, password) => 
  api.post('/api/auth/login', { email, password })

export const register = (email, username, password) => 
  api.post('/api/auth/register', { email, username, password })

export const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

// 邮件API
export const getMails = (folder, page = 1, pageSize = 20) => 
  api.get(`/api/mail/${folder}`, { params: { page, page_size: pageSize } })

export const getMail = (id) => 
  api.get(`/api/mail/${id}`)

export const sendMail = (data) => 
  api.post('/api/mail/send', data)

export const deleteMail = (id) => 
  api.delete(`/api/mail/${id}`)

export const markAsRead = (id) => 
  api.post(`/api/mail/${id}/read`)

export const toggleStar = (id) => 
  api.post(`/api/mail/${id}/star`)

export const recallMail = (id) => 
  api.post(`/api/mail/${id}/recall`)

export const searchMails = (keyword, page = 1, pageSize = 20) => 
  api.get('/api/mail/search', { params: { keyword, page, page_size: pageSize } })

export const quickReply = (mailId, body) => 
  api.post(`/api/mail/${mailId}/reply`, { body })

export const markAsTodo = (id) => 
  api.post(`/api/mail/${id}/todo`)

// 群组API
export const getGroups = () => 
  api.get('/api/groups')

export const createGroup = (name, members) => 
  api.post('/api/groups', { name, members })

export const deleteGroup = (id) => 
  api.delete(`/api/groups/${id}`)

// 附件API
export const uploadAttachment = (formData) => 
  api.post('/api/mail/attachment', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

export const downloadAttachment = (attachmentId) => 
  api.get(`/api/mail/attachment/${attachmentId}`, { 
    responseType: 'blob' 
  })

export default api