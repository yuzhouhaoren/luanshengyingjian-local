<template>
  <div class="match-pool-container">
    <!-- 正十二面体动画 -->
    <DodecahedronAnimation />
    
    
      <h1>匹配池</h1>
      
      <div class="pool-content">
        <div class="countdown-text">
          <p class="countdown-label">距离下一次分配</p>
          <div class="countdown-time">
            <span class="time-unit">
              <span class="time-value">{{ countdown.days }}</span>
              <span class="time-label">天</span>
            </span>
            <span class="time-separator">:</span>
            <span class="time-unit">
              <span class="time-value">{{ countdown.hours }}</span>
              <span class="time-label">时</span>
            </span>
            <span class="time-separator">:</span>
            <span class="time-unit">
              <span class="time-value">{{ countdown.minutes }}</span>
              <span class="time-label">分</span>
            </span>
          </div>
          <p class="match-schedule">匹配时间：每周二、周五 0:00</p>
        </div>
      </div>
      
      <div class="match-results" v-if="matchResults.length > 0">
        <h2>我的匹配结果</h2>
        <div class="results-list">
          <div class="result-card" v-for="result in matchResults" :key="result.id">
            <div class="result-avatar">{{ result.matched_user_name.charAt(0) }}</div>
            <div class="result-info">
              <h3>{{ result.matched_user_name }}</h3>
              <p>匹配度：{{ result.match_score }}%</p>
              <p>交友目的：{{ result.intent_type || '朋友' }}</p>
              <p>邮箱：{{ result.email }}</p>
              <p class="match-time">{{ formatTime(result.created_at) }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="no-results" v-else>
        <p>暂无匹配结果，请等待下一次分配</p>
      </div>
    
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import DodecahedronAnimation from '../components/DodecahedronAnimation.vue'

const countdown = ref({
  days: 0,
  hours: 0,
  minutes: 0
})

const matchResults = ref([])
let timer = null

const calculateNextMatch = () => {
  const now = new Date()
  const dayOfWeek = now.getDay()
  const hours = now.getHours()
  const minutes = now.getMinutes()
  
  let daysUntilNextMatch = 0
  let targetDay = 0
  
  if (dayOfWeek === 2) {
    if (hours < 0 || (hours === 0 && minutes === 0)) {
      targetDay = 2
    } else {
      targetDay = 5
    }
  } else if (dayOfWeek === 5) {
    if (hours < 0 || (hours === 0 && minutes === 0)) {
      targetDay = 5
    } else {
      targetDay = 2
      daysUntilNextMatch = 4
    }
  } else if (dayOfWeek < 2) {
    targetDay = 2
    daysUntilNextMatch = 2 - dayOfWeek
  } else if (dayOfWeek < 5) {
    targetDay = 5
    daysUntilNextMatch = 5 - dayOfWeek
  } else {
    targetDay = 2
    daysUntilNextMatch = 2 + (7 - dayOfWeek)
  }
  
  const nextMatch = new Date(now)
  nextMatch.setDate(now.getDate() + daysUntilNextMatch)
  nextMatch.setHours(0, 0, 0, 0)
  
  const diff = nextMatch - now
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hoursLeft = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutesLeft = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  countdown.value = {
    days: days,
    hours: hoursLeft,
    minutes: minutesLeft
  }
}

const fetchMatchResults = async () => {
  try {
    const userId = localStorage.getItem('userId')
    if (!userId) return
    
    const response = await axios.get(`http://localhost:5000/api/matches/${userId}`)
    if (response.data.status === 'success') {
      matchResults.value = response.data.matches
    }
  } catch (error) {
    console.error('获取匹配结果失败:', error)
  }
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}



onMounted(() => {
  calculateNextMatch()
  timer = setInterval(calculateNextMatch, 60000)
  fetchMatchResults()
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.match-pool-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

.glass-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
  position: relative;
  z-index: 10;
}

h1 {
  text-align: center;
  font-size: 32px;
  color: #1E293B;
  margin-bottom: 40px;
}

.pool-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
}





.countdown-text {
  text-align: center;
}

.countdown-label {
  font-size: 18px;
  color: #64748B;
  margin-bottom: 15px;
}

.countdown-time {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 15px;
}

.time-unit {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.time-value {
  font-size: 48px;
  font-weight: bold;
  color: #2563EB;
  background: rgba(37, 99, 235, 0.1);
  padding: 10px 20px;
  border-radius: 10px;
  min-width: 80px;
  text-align: center;
}

.time-label {
  font-size: 14px;
  color: #64748B;
  margin-top: 5px;
}

.time-separator {
  font-size: 36px;
  color: #2563EB;
  font-weight: bold;
}

.match-schedule {
  font-size: 14px;
  color: #94A3B8;
  margin-top: 10px;
}

.match-results {
  margin-top: 40px;
}

.match-results h2 {
  font-size: 24px;
  color: #1E293B;
  margin-bottom: 20px;
  text-align: center;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-card {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.3);
  padding: 20px;
  border-radius: 15px;
  gap: 20px;
}

.result-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  flex-shrink: 0;
}

.result-info {
  flex: 1;
}

.result-info h3 {
  font-size: 18px;
  color: #1E293B;
  margin-bottom: 5px;
}

.result-info p {
  font-size: 14px;
  color: #64748B;
  margin: 3px 0;
}

.match-time {
  font-size: 12px !important;
  color: #94A3B8 !important;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.btn-accept,
.btn-reject {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
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

.no-results {
  text-align: center;
  padding: 40px;
  color: #64748B;
}

.no-results p {
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .glass-card {
    padding: 30px;
  }
  
  h1 {
    font-size: 24px;
  }
  
  .geometric-animation {
    width: 150px;
    height: 150px;
  }
  
  .time-value {
    font-size: 36px;
    padding: 8px 15px;
    min-width: 60px;
  }
  
  .time-separator {
    font-size: 28px;
  }
  
  .result-card {
    flex-direction: column;
    text-align: center;
  }
  
  .result-actions {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .glass-card {
    padding: 20px;
  }
  
  h1 {
    font-size: 20px;
  }
  
  .geometric-animation {
    width: 120px;
    height: 120px;
  }
  
  .time-value {
    font-size: 28px;
    padding: 6px 12px;
    min-width: 50px;
  }
  
  .time-separator {
    font-size: 22px;
  }
  
  .countdown-time {
    gap: 5px;
  }
  
  .countdown-label {
    font-size: 16px;
  }
  
  .match-schedule {
    font-size: 12px;
  }
  
  .result-card {
    padding: 15px;
  }
  
  .result-avatar {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }
  
  .result-info h3 {
    font-size: 16px;
  }
  
  .result-info p {
    font-size: 13px;
  }
}
</style>
