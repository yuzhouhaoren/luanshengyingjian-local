<template>
  <div class="user-container">
    <div class="user-header">
      <div class="header-top">
        <div class="user-info">
          <div class="avatar-section">
            <img :src="user.avatar || defaultAvatar" alt="头像" class="avatar">
            <input type="file" id="avatar-upload" class="avatar-upload" @change="handleAvatarUpload">
            <label for="avatar-upload" class="avatar-edit">
              <span>📷</span>
            </label>
          </div>
          <div class="user-details">
            <h1 class="username">{{ user.username || '用户' }}</h1>
            <p class="user-id">ID: {{ user.id || '加载中...' }}</p>
          </div>
        </div>
        <div class="header-actions">
          <div class="message-icon" @click="toggleMessages">
            <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
              <polyline points="22,6 12,13 2,6"></polyline>
            </svg>
            <span v-if="notificationCount > 0" class="message-badge">{{ notificationCount }}</span>
          </div>
        </div>
      </div>
      
      <div class="user-stats">
        <div class="stat-item">
          <span class="stat-value">{{ stats.matchCount }}</span>
          <span class="stat-label">匹配</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.friendCount }}</span>
          <span class="stat-label">好友</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.postCount }}</span>
          <span class="stat-label">帖子</span>
        </div>
      </div>
    </div>
    
    <!-- 消息面板 -->
    <div v-if="showMessages" class="messages-panel">
      <div class="messages-header">
        <h3>消息通知</h3>
        <button class="close-btn" @click="toggleMessages">✕</button>
      </div>
      
      <div class="messages-tabs">
        <button :class="{ active: activeTab === 'matches' }" @click="activeTab = 'matches'">匹配结果</button>
        <button :class="{ active: activeTab === 'requests' }" @click="activeTab = 'requests'">交友申请</button>
      </div>
      
      <div class="messages-content">
        <!-- 匹配结果 -->
        <div v-if="activeTab === 'matches'" class="matches-list">
          <div v-if="matchResults.length === 0" class="empty-message">
            <p>暂无匹配结果</p>
          </div>
          <div v-else class="message-item" v-for="match in matchResults" :key="match.id">
            <div class="message-avatar">{{ match.matched_user_name.charAt(0) }}</div>
            <div class="message-info">
              <h4>{{ match.matched_user_name }}</h4>
              <p>交友目的：{{ match.intent_type || '朋友' }}</p>
              <p>邮箱：{{ match.email }}</p>
              <span class="message-time">{{ formatTime(match.created_at) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 交友申请 -->
        <div v-if="activeTab === 'requests'" class="requests-list">
          <div v-if="friendRequests.length === 0" class="empty-message">
            <p>暂无交友申请</p>
          </div>
          <div v-else class="message-item" v-for="request in friendRequests" :key="request.id">
            <div class="message-avatar">{{ request.from_user_name.charAt(0) }}</div>
            <div class="message-info">
              <h4>{{ request.from_user_name }}</h4>
              <p>交友目的：{{ request.intent_type || '朋友' }}</p>
              <span class="message-time">{{ formatTime(request.created_at) }}</span>
            </div>
            <div class="message-actions">
              <button class="btn-accept" @click="acceptRequest(request)">接受</button>
              <button class="btn-reject" @click="rejectRequest(request)">拒绝</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 个人信息卡片 -->
    <div class="profile-card">
      <div class="card-header">
        <h3>个人信息</h3>
      </div>
      <div class="profile-info">
        <div class="info-item">
          <span class="info-label">年龄</span>
          <span class="info-value">{{ user.age || '未设置' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">性别</span>
          <span class="info-value">{{ user.gender || '未设置' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">职业</span>
          <span class="info-value">{{ user.occupation || '未设置' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">性取向</span>
          <span class="info-value">{{ user.sexual_orientation || '未设置' }}</span>
        </div>
        <div class="info-item full-width">
          <span class="info-label">兴趣爱好</span>
          <div class="hobbies-tags">
            <span v-for="hobby in hobbiesList" :key="hobby" class="hobby-tag">{{ hobby }}</span>
            <span v-if="hobbiesList.length === 0" class="info-value">未设置</span>
          </div>
        </div>
        <div class="info-item full-width">
          <span class="info-label">性格特点</span>
          <span class="info-value">{{ user.personality || '未设置' }}</span>
        </div>
      </div>
    </div>
    
    <!-- 性格画像卡片 -->
    <div class="personality-card" v-if="hasPersonalityScores">
      <div class="card-header">
        <h3>性格画像</h3>
      </div>
      <div class="personality-chart">
        <canvas ref="personalityCanvas"></canvas>
      </div>
    </div>
    
    <!-- 发布帖子卡片 -->
    <div class="post-card">
      <div class="card-header">
        <h3>发布新帖子</h3>
      </div>
      <div class="post-form">
        <div class="form-group">
          <label for="post-title">标题</label>
          <input type="text" id="post-title" v-model="newPost.title" placeholder="请输入帖子标题">
        </div>
        <div class="form-group">
          <label for="post-content">内容</label>
          <textarea id="post-content" v-model="newPost.content" placeholder="请输入帖子内容"></textarea>
        </div>
        <div class="form-group">
          <label for="post-tags">标签（用逗号分隔）</label>
          <input type="text" id="post-tags" v-model="newPost.tagsInput" placeholder="例如：户外,爬山,旅行">
        </div>
        <button class="btn-publish" @click="publishPost">发布帖子</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'

const user = ref({
  id: '',
  username: '',
  name: '',
  age: null,
  gender: '',
  occupation: '',
  sexual_orientation: '',
  hobbies: '',
  personality: '',
  avatar: ''
})

const defaultAvatar = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=default%20user%20avatar&image_size=square'
const showMessages = ref(false)
const activeTab = ref('matches')
const matchResults = ref([])
const friendRequests = ref([])
const notificationCount = ref(0)
const personalityCanvas = ref(null)
let personalityChart = null

const stats = ref({
  matchCount: 0,
  friendCount: 0,
  postCount: 0
})

const newPost = ref({
  title: '',
  content: '',
  tagsInput: ''
})

const hobbiesList = computed(() => {
  if (!user.value.hobbies) return []
  return user.value.hobbies.split(',').filter(h => h.trim())
})

const hasPersonalityScores = computed(() => {
  return user.value.profile_scores && Object.keys(user.value.profile_scores).length > 0
})

const loadUserProfile = async () => {
  const savedUser = localStorage.getItem('user')
  if (!savedUser) return
  
  const userObj = JSON.parse(savedUser)
  const userId = userObj.id
  
  // 先显示本地存储的基本信息
  user.value = {
    ...user.value,
    id: userId,
    username: userObj.username,
    email: userObj.email
  }
  
  try {
    const response = await axios.get(`http://localhost:5000/api/profile/${userId}`)
    if (response.data.status === 'success' && response.data.profile) {
      const profile = response.data.profile
      user.value = {
        id: userId,
        username: profile.username || userObj.username || '',
        age: profile.age,
        gender: profile.gender || '',
        occupation: profile.occupation || '',
        sexual_orientation: profile.sexual_orientation || '',
        hobbies: profile.hobbies || '',
        personality: profile.personality || '',
        avatar: profile.avatar ? `http://localhost:5000/avatars/${profile.avatar}` : defaultAvatar,
        profile_scores: profile.profile_scores ? JSON.parse(profile.profile_scores) : {}
      }
      
      if (hasPersonalityScores.value) {
        setTimeout(() => renderPersonalityChart(), 100)
      }
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
    // 即使API调用失败，也保持本地存储的基本信息
    user.value = {
      ...user.value,
      avatar: defaultAvatar
    }
  }
  
  // 加载用户帖子数量
  loadUserPostCount()
}

const loadUserPostCount = async () => {
  const savedUser = localStorage.getItem('user')
  if (!savedUser) return
  
  const userObj = JSON.parse(savedUser)
  const userId = userObj.id
  
  try {
    const response = await axios.get(`http://localhost:5000/api/posts/user/${userId}`)
    if (response.data.status === 'success') {
      stats.value.postCount = response.data.count
    }
  } catch (error) {
    console.error('加载用户帖子数量失败:', error)
  }
}

const loadNotifications = async () => {
  const savedUser = localStorage.getItem('user')
  if (!savedUser) return
  
  const userObj = JSON.parse(savedUser)
  const userId = userObj.id
  
  try {
    const response = await axios.get(`http://localhost:5000/api/notifications/${userId}`)
    if (response.data.status === 'success') {
      notificationCount.value = response.data.data.total
    }
  } catch (error) {
    console.error('加载通知数量失败:', error)
  }
}

const loadMatchResults = async () => {
  const savedUser = localStorage.getItem('user')
  if (!savedUser) return
  
  const userObj = JSON.parse(savedUser)
  const userId = userObj.id
  
  try {
    const response = await axios.get(`http://localhost:5000/api/matches/${userId}`)
    if (response.data.status === 'success') {
      matchResults.value = response.data.matches
    }
  } catch (error) {
    console.error('加载匹配结果失败:', error)
  }
}

const loadFriendRequests = async () => {
  const savedUser = localStorage.getItem('user')
  if (!savedUser) return
  
  const userObj = JSON.parse(savedUser)
  const userId = userObj.id
  
  try {
    const response = await axios.get(`http://localhost:5000/api/friend-requests/${userId}`)
    if (response.data.status === 'success') {
      friendRequests.value = response.data.requests
    }
  } catch (error) {
    console.error('加载交友申请失败:', error)
  }
}

const toggleMessages = () => {
  showMessages.value = !showMessages.value
  if (showMessages.value) {
    loadMatchResults()
    loadFriendRequests()
  }
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const acceptMatch = async (match) => {
  try {
    await axios.post('http://localhost:5000/api/matches/accept', { match_id: match.id })
    loadMatchResults()
    loadNotifications()
  } catch (error) {
    console.error('接受匹配失败:', error)
  }
}

const rejectMatch = async (match) => {
  try {
    await axios.post('http://localhost:5000/api/matches/reject', { match_id: match.id })
    loadMatchResults()
    loadNotifications()
  } catch (error) {
    console.error('拒绝匹配失败:', error)
  }
}

const acceptRequest = async (request) => {
  try {
    await axios.post('http://localhost:5000/api/friend-request/accept', { request_id: request.id })
    loadFriendRequests()
    loadNotifications()
  } catch (error) {
    console.error('接受申请失败:', error)
  }
}

const rejectRequest = async (request) => {
  try {
    await axios.post('http://localhost:5000/api/friend-request/reject', { request_id: request.id })
    loadFriendRequests()
    loadNotifications()
  } catch (error) {
    console.error('拒绝申请失败:', error)
  }
}

const handleAvatarUpload = async (event) => {
  const file = event.target.files[0]
  if (file) {
    const formData = new FormData()
    formData.append('avatar', file)
    formData.append('user_id', user.value.id)
    
    try {
      const response = await axios.post('http://localhost:5000/api/avatar/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      if (response.data.status === 'success') {
        user.value.avatar = `http://localhost:5000${response.data.avatar_path}`
        // 触发全局事件，通知App.vue更新头像
        window.dispatchEvent(new CustomEvent('avatar-updated', { 
          detail: { avatar: user.value.avatar } 
        }))
        alert('头像上传成功！')
      } else {
        alert('上传失败：' + (response.data.message || '未知错误'))
      }
    } catch (error) {
      console.error('上传头像失败:', error)
      alert('上传失败，请稍后重试')
    }
  }
}



const renderPersonalityChart = () => {
  if (!personalityCanvas.value || !user.value.profile_scores) return
  
  if (personalityChart) {
    personalityChart.destroy()
  }
  
  const scores = user.value.profile_scores
  const labels = ['外向性', '开放性', '尽责性', '宜人性', '神经质', '自恋']
  const data = [
    scores.extraversion || 0,
    scores.openness || 0,
    scores.conscientiousness || 0,
    scores.agreeableness || 0,
    scores.neuroticism || 0,
    scores.narcissism || 0
  ]
  
  personalityChart = new Chart(personalityCanvas.value, {
    type: 'radar',
    data: {
      labels: labels,
      datasets: [{
        label: '性格得分',
        data: data,
        fill: true,
        backgroundColor: 'rgba(37, 99, 235, 0.2)',
        borderColor: '#2563EB',
        pointBackgroundColor: '#2563EB',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#2563EB'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          beginAtZero: true,
          max: 5,
          ticks: {
            stepSize: 1
          }
        }
      }
    }
  })
}

const publishPost = async () => {
  const savedUser = localStorage.getItem('user')
  if (!savedUser) {
    alert('请先登录')
    return
  }
  
  if (!newPost.value.title || !newPost.value.content) {
    alert('请填写标题和内容')
    return
  }
  
  const userObj = JSON.parse(savedUser)
  const userId = userObj.id
  
  // 处理标签
  const tags = newPost.value.tagsInput
    ? newPost.value.tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag)
    : []
  
  try {
    const response = await axios.post('http://localhost:5000/api/posts/publish', {
      user_id: userId,
      title: newPost.value.title,
      content: newPost.value.content,
      tags: tags
    })
    
    if (response.data.status === 'success') {
      alert('帖子发布成功！')
      // 重置表单
      newPost.value = {
        title: '',
        content: '',
        tagsInput: ''
      }
      // 更新帖子数量
      loadUserPostCount()
    } else {
      alert('发布失败：' + (response.data.message || '未知错误'))
    }
  } catch (error) {
    console.error('发布帖子失败:', error)
    alert('发布失败，请稍后重试')
  }
}

onMounted(() => {
  loadUserProfile()
  loadNotifications()
})
</script>

<style scoped>
.user-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.user-header {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 30px;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar-section {
  position: relative;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #2563EB;
}

.avatar-upload {
  display: none;
}

.avatar-edit {
  position: absolute;
  bottom: 0;
  right: 0;
  background: #2563EB;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.avatar-edit:hover {
  background: #1d4ed8;
  transform: scale(1.1);
}

.user-details h1 {
  font-size: 24px;
  color: #1E293B;
  margin-bottom: 5px;
}

.user-id {
  font-size: 14px;
  color: #64748B;
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.message-icon {
  position: relative;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  background: rgba(37, 99, 235, 0.1);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-svg {
  width: 24px;
  height: 24px;
  color: #2563EB;
}

.message-icon:hover {
  background: rgba(37, 99, 235, 0.2);
  transform: scale(1.1);
}

.message-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #EF4444;
  color: white;
  font-size: 12px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}



.user-stats {
  display: flex;
  justify-content: space-around;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #2563EB;
}

.stat-label {
  font-size: 14px;
  color: #64748B;
}

.messages-panel {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.messages-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.messages-header h3 {
  font-size: 18px;
  color: #1E293B;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #64748B;
  transition: all 0.3s ease;
}

.close-btn:hover {
  color: #1E293B;
  transform: scale(1.1);
}

.messages-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.messages-tabs button {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 10px;
  background: rgba(37, 99, 235, 0.1);
  color: #2563EB;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.messages-tabs button.active {
  background: #2563EB;
  color: white;
}

.messages-tabs button:hover:not(.active) {
  background: rgba(37, 99, 235, 0.2);
}

.messages-content {
  max-height: 400px;
  overflow-y: auto;
}

.empty-message {
  text-align: center;
  padding: 40px;
  color: #64748B;
}

.message-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 15px;
  margin-bottom: 10px;
}

.message-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  flex-shrink: 0;
}

.message-info {
  flex: 1;
}

.message-info h4 {
  font-size: 16px;
  color: #1E293B;
  margin-bottom: 5px;
}

.message-info p {
  font-size: 14px;
  color: #64748B;
  margin-bottom: 3px;
}

.message-time {
  font-size: 12px;
  color: #94A3B8;
}

.message-actions {
  display: flex;
  gap: 8px;
}

.btn-accept,
.btn-reject {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s ease;
}

.btn-accept {
  background: #10B981;
  color: white;
}

.btn-accept:hover {
  background: #059669;
  transform: translateY(-2px);
}

.btn-reject {
  background: #EF4444;
  color: white;
}

.btn-reject:hover {
  background: #DC2626;
  transform: translateY(-2px);
}

.profile-card,
.personality-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.card-header h3 {
  font-size: 18px;
  color: #1E293B;
}

.edit-link {
  color: #2563EB;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s ease;
}

.edit-link:hover {
  color: #1d4ed8;
}

.profile-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-item.full-width {
  grid-column: span 2;
}

.info-label {
  font-size: 14px;
  color: #64748B;
}

.info-value {
  font-size: 16px;
  color: #1E293B;
}

.hobbies-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hobby-tag {
  background: rgba(37, 99, 235, 0.1);
  color: #2563EB;
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 14px;
}

.personality-chart {
  height: 300px;
}

/* 发布帖子卡片样式 */
.post-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.post-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.post-form .form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.post-form label {
  font-size: 14px;
  font-weight: 600;
  color: #64748B;
}

.post-form input,
.post-form textarea {
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(5px);
  font-size: 16px;
  transition: all 0.3s ease;
}

.post-form input:focus,
.post-form textarea:focus {
  outline: none;
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}

.post-form textarea {
  resize: vertical;
  min-height: 120px;
}

.btn-publish {
  padding: 12px 24px;
  background: linear-gradient(135deg, #2563EB, #3B82F6);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  align-self: flex-start;
}

.btn-publish:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-header {
    padding: 20px;
  }
  
  .avatar {
    width: 60px;
    height: 60px;
  }
  
  .user-details h1 {
    font-size: 20px;
  }
  
  .profile-info {
    grid-template-columns: 1fr;
  }
  
  .info-item.full-width {
    grid-column: span 1;
  }
  
  .message-item {
    flex-direction: column;
    text-align: center;
  }
  
  .message-actions {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .user-container {
    padding: 10px;
  }
  
  .user-header {
    padding: 15px;
  }
  
  .header-top {
    flex-direction: column;
    align-items: center;
    gap: 15px;
  }
  
  .user-info {
    flex-direction: column;
    text-align: center;
  }
  
  .avatar {
    width: 80px;
    height: 80px;
  }
  
  .user-stats {
    gap: 20px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .messages-tabs button {
    padding: 8px;
    font-size: 14px;
  }
}
</style>
