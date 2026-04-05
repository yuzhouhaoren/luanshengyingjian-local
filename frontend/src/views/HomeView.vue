<template>
  <div class="home">
    <!-- 粒子效果层 -->
    <div class="particles">
      <span v-for="i in 20" :key="i" class="particle" :style="{ '--delay': i * 0.5 + 's', '--x': Math.random() * 100 + '%', '--y': Math.random() * 100 + '%' }"></span>
    </div>
    
    <!-- 数据大屏容器 -->
    <div class="dashboard-container">
      <!-- 顶部标题栏 -->
      <header class="dashboard-header glass-effect">
        <div class="header-left">
          <h1 class="dashboard-title">孪生映见</h1>
          <span class="dashboard-subtitle">实时数据监控平台</span>
        </div>
        <div class="header-center">
          <div class="current-time">{{ currentTime }}</div>
        </div>
        <div class="header-right">
          <div class="auth-buttons">
            <button v-if="user" @click="toggleSidebar" class="btn-icon sidebar-toggle" title="菜单">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
            <template v-else>
              <router-link to="/register" class="btn primary">开始注册</router-link>
              <router-link to="/login" class="btn secondary">登录</router-link>
            </template>
          </div>
        </div>
      </header>

      <!-- 主要内容区域 -->
      <main class="dashboard-main">
        <!-- 左侧面板 -->
        <aside class="left-panel">
          <div class="stat-card glass-effect">
            <div class="stat-icon users-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ matchStats.total_users }}</div>
              <div class="stat-label">注册用户总数</div>
            </div>
          </div>

          <div class="stat-card glass-effect">
            <div class="stat-icon match-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ matchStats.matched_pairs }}</div>
              <div class="stat-label">匹配成功对数</div>
            </div>
          </div>

          <div class="chart-card glass-effect">
            <h3 class="card-title">
              <span class="title-icon pulse-icon"></span>
              最近匹配记录
            </h3>
            <div class="chart-wrapper">
              <canvas ref="lineChart"></canvas>
            </div>
          </div>

          <div class="chart-card glass-effect">
            <h3 class="card-title">
              <span class="title-icon bar-icon"></span>
              个人属性分析
            </h3>
            <div class="chart-wrapper radar-chart">
              <canvas ref="radarChart"></canvas>
            </div>
          </div>
        </aside>

        <!-- 中间区域 - 中国地图 -->
        <section class="center-map-area">
          <div class="map-card glass-effect">
            <h2 class="map-title">
              <span class="map-icon pulse-glow"></span>
              中国用户分布热力图
            </h2>
            <div id="china-map" class="map-container"></div>
            <div v-if="mapError" class="map-error">
              <p>⚠️ 地图加载失败</p>
              <small>请检查网络连接或配置高德地图API密钥</small>
            </div>
          </div>
        </section>

        <!-- 右侧面板 -->
        <aside class="right-panel">
          <div class="stat-card glass-effect">
            <div class="stat-icon active-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ activeUsers }}</div>
              <div class="stat-label">今日活跃用户</div>
            </div>
          </div>

          <div class="stat-card glass-effect">
            <div class="stat-icon chat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ chatCount }}</div>
              <div class="stat-label">今日聊天次数</div>
            </div>
          </div>

          <div class="chart-card glass-effect">
            <h3 class="card-title">
              <span class="title-icon pie-icon"></span>
              平台性格分布
            </h3>
            <div class="chart-wrapper pie-chart">
              <canvas ref="pieChart"></canvas>
            </div>
          </div>
        </aside>
      </main>

    <!-- 核心特性区域 - 移到数据监控平台下方 -->
    <section class="features-section-hud">
      <div class="hud-container">
        <div class="hud-corner hud-tl"></div>
        <div class="hud-corner hud-tr"></div>
        <div class="hud-corner hud-bl"></div>
        <div class="hud-corner hud-br"></div>
        
        <h3 class="hud-title">
          <span class="hud-line left"></span>
          <span class="hud-text">CORE FEATURES // 核心特性</span>
          <span class="hud-line right"></span>
        </h3>
        
        <div class="features-grid-hud">
          <div class="feature-card-hud" v-for="(feature, index) in features" :key="index">
            <div class="feature-glow" :style="{ background: feature.color }"></div>
            <div class="feature-icon-hud" :style="{ borderColor: feature.color, color: feature.color }">
              <component :is="'svg'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path v-if="feature.icon === 'ai'" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                <template v-else-if="feature.icon === 'twin'">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </template>
                <path v-else-if="feature.icon === 'security'" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path v-else d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </component>
            </div>
            <div class="feature-content-hud">
              <h4 class="feature-name-hud">{{ feature.name }}</h4>
              <p class="feature-desc-hud">{{ feature.desc }}</p>
            </div>
            <div class="feature-status" :style="{ color: feature.color }">
              <span class="status-dot"></span>
              ACTIVE
            </div>
          </div>
        </div>
      </div>
    </section>
    </div>

    <!-- Sidebar 通过Teleport传送到body -->
    <Teleport to="body">
      <div v-if="showSidebar" class="__sidebar_backdrop" @click="closeSidebar"></div>
      <aside v-if="showSidebar" class="__sidebar_panel">
        <div class="__sidebar_inner">
          <div class="__sidebar_header">
            <div class="__sidebar_user_info" v-if="user">
              <div class="__user_avatar_small">
                {{ (user.username || user.email || 'U').charAt(0).toUpperCase() }}
              </div>
              <div class="__user_detail">
                <span class="__user_name">{{ user.username || '用户' }}</span>
                <span class="__user_email">{{ user.email || '' }}</span>
              </div>
            </div>
            <button @click="closeSidebar" class="__close_btn">&times;</button>
          </div>
          <nav class="__sidebar_nav">
            <router-link to="/profile" @click="closeSidebar" class="__sidebar_item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              个人中心
            </router-link>
            <a href="#" @click.prevent="handleChatNav" class="__sidebar_item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
              </svg>
              聊天广场
            </a>
            <a href="#" @click.prevent="handleMatchesNav" class="__sidebar_item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8.5" cy="7" r="4"></circle>
                <path d="M20 8.5V21"></path>
                <path d="M20 8.5c0 2.5-2 4.5-4.5 4.5S11 11 11 8.5 13 4 15.5 4 20 6 20 8.5z"></path>
              </svg>
              我的匹配
            </a>
            <div class="__sidebar_divider"></div>
            <a href="#" @click.prevent="logout" class="__sidebar_item __logout_item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
              退出登录
            </a>
          </nav>
        </div>
      </aside>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import Chart from 'chart.js/auto'

const router = useRouter()
const route = useRoute()
const user = ref(null)
const showSidebar = ref(false)
const matchStats = ref({
  total_users: 0,
  matched_pairs: 0,
  daily_matches: [],
  recent_matches: []
})

const activeUsers = ref(0)
const chatCount = ref(0)
const currentTime = ref('')
const mapError = ref(false)

const lineChart = ref(null)
const radarChart = ref(null)
const pieChart = ref(null)

let lineChartInstance = null
let radarChartInstance = null
let pieChartInstance = null
let mapInstance = null

const features = ref([
  {
    name: 'AI智能匹配',
    desc: '基于用户性格画像与兴趣标签的智能推荐算法，综合分析外向性、开放性、尽责性等多维人格特征，为您精准推荐志趣相投的匹配对象',
    icon: 'ai',
    color: '#2563EB'
  },
  {
    name: '数字孪生社区',
    desc: '构建数字孪生身份体系，每位用户拥有独立的数字化身，支持虚拟形象交互与社区动态分享，打造沉浸式社交体验空间',
    icon: 'twin',
    color: '#DC2626'
  },
  {
    name: '隐私安全保护',
    desc: '采用HTTPS加密传输与数据脱敏存储机制，严格遵循最小权限原则，确保用户个人信息与社交数据的安全性与私密性',
    icon: 'security',
    color: '#059669'
  },
  {
    name: '数据分析看板',
    desc: '实时统计平台核心运营指标，包括用户增长趋势、匹配成功率、活跃度分布等关键数据，以可视化图表形式直观呈现',
    icon: 'real',
    color: '#D97706'
  }
])

const updateTime = () => {
  const now = new Date()
  const options = { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit',
    hour12: false 
  }
  currentTime.value = now.toLocaleString('zh-CN', options).replace(/\//g, '-')
}

const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
  if (showSidebar.value) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
}

const closeSidebar = () => {
  showSidebar.value = false
  document.body.style.overflow = ''
}

const handleChatNav = () => {
  closeSidebar()
  alert('聊天功能开发中...')
}

const handleMatchesNav = () => {
  closeSidebar()
  alert('匹配功能开发中...')
}

const logout = () => {
  localStorage.removeItem('user')
  user.value = null
  closeSidebar()
  router.push('/login')
}

onMounted(async () => {
  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    user.value = JSON.parse(savedUser)
  }
  
  updateTime()
  setInterval(updateTime, 1000)
  
  await fetchStats()
  
  await nextTick()
  initCharts()
  
  initMap()
})

onUnmounted(() => {
  if (mapInstance) {
    mapInstance.destroy()
  }
  document.body.style.overflow = ''
})

watch(() => route.path, (newPath) => {
  if (newPath === '/') {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      user.value = JSON.parse(savedUser)
    } else {
      user.value = null
    }
    
    fetchStats()
  }
})

const userPersonality = ref({
  extraversion: 0,
  openness: 0,
  conscientiousness: 0,
  agreeableness: 0,
  neuroticism: 0,
  narcissism: 0
})

const platformPersonality = ref({
  extraversion: 0,
  openness: 0,
  conscientiousness: 0,
  agreeableness: 0,
  neuroticism: 0,
  narcissism: 0
})

const fetchStats = async () => {
  try {
    console.log('开始获取统计数据...');
    const response = await axios.get('http://localhost:5000/api/stats')
    console.log('获取统计数据成功:', response.data);
    if (response.data.status === 'success') {
      matchStats.value.total_users = response.data.data.total_users
      matchStats.value.matched_pairs = response.data.data.matched_pairs
      matchStats.value.daily_matches = response.data.data.daily_matches
      
      const recentData = []
      for (let i = 1; i <= 10; i++) {
        recentData.push({
          index: i,
          pairs: Math.floor(Math.random() * 20) + 5
        })
      }
      matchStats.value.recent_matches = recentData
      
      activeUsers.value = response.data.data.active_users || Math.floor(matchStats.value.total_users * 0.6)
      chatCount.value = response.data.data.chat_count || Math.floor(matchStats.value.matched_pairs * 10)
      console.log('更新统计数据:', matchStats.value);
    } else {
      matchStats.value.total_users = 0
      matchStats.value.matched_pairs = 0
      matchStats.value.daily_matches = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
      
      matchStats.value.recent_matches = Array.from({length: 10}, (_, i) => ({
        index: i + 1,
        pairs: 0
      }))
      
      activeUsers.value = 0
      chatCount.value = 0
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    matchStats.value.total_users = 0
    matchStats.value.matched_pairs = 0
    matchStats.value.daily_matches = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    matchStats.value.recent_matches = Array.from({length: 10}, (_, i) => ({
      index: i + 1,
      pairs: 0
    }))
    
    activeUsers.value = 0
    chatCount.value = 0
  }
  
  if (user.value) {
    try {
      const profileResponse = await axios.get(`http://localhost:5000/api/profile/${user.value.id}`)
      if (profileResponse.data.status === 'success' && profileResponse.data.profile) {
        const profile = profileResponse.data.profile
        if (profile.profile_scores) {
          const scores = profile.profile_scores
          userPersonality.value = {
            extraversion: scores.extraversion || 0,
            openness: scores.openness || 0,
            conscientiousness: scores.conscientiousness || 0,
            agreeableness: scores.agreeableness || 0,
            neuroticism: scores.neuroticism || 0,
            narcissism: scores.narcissism || 0
          }
          console.log('获取用户个人画像数据成功:', userPersonality.value);
        }
      }
    } catch (error) {
      console.error('获取用户个人画像数据失败:', error)
    }
  }
  
  try {
    const platformResponse = await axios.get('http://localhost:5000/api/personality/stats')
    if (platformResponse.data.status === 'success') {
      platformPersonality.value = platformResponse.data.data
      console.log('获取平台性格分布数据成功:', platformPersonality.value);
    }
  } catch (error) {
    console.error('获取平台性格分布数据失败:', error)
  }
  
  updateCharts()
  console.log('图表数据已更新');
}

const initMap = () => {
  mapError.value = false;
  
  window._AMapSecurityConfig = {
    securityJsCode: '0c57b9be0dd1c90803aa88d89cbc25e2'
  };
  
  if (typeof AMapLoader === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://webapi.amap.com/loader.js';
    script.onload = () => {
      loadMap();
    };
    script.onerror = () => {
      console.error('地图SDK加载失败');
      mapError.value = true;
    };
    document.head.appendChild(script);
  } else {
    loadMap();
  }
};

const loadMap = () => {
  AMapLoader.load({
    key: '0c57b9be0dd1c90803aa88d89cbc25e2',
    version: '2.0',
    plugins: ['AMap.HeatMap', 'AMap.DistrictLayer']
  }).then((AMap) => {
    mapInstance = new AMap.Map('china-map', {
      viewMode: '3D',
      zoom: 4,
      center: [104.195, 35.861],
      mapStyle: 'amap://styles/normal',
      backgroundColor: 'transparent'
    });
    
    const mapContainer = document.getElementById('china-map')
    if (mapContainer) {
      mapContainer.style.backgroundColor = 'transparent'
    }

    const districtLayer = new AMap.DistrictLayer.Country({
      zIndex: 12,
      SOC: 'CHN',
      depth: 2,
      styles: {
        fill: function(props) {
          return 'rgba(160, 180, 200, 0.1)'
        },
        'stroke-width': 1.5,
        stroke: '#475569',
        'nation-stroke': '#1E293B',
        'province-stroke': '#334155',
        'city-stroke': '#64748B',
        'coastline-stroke': '#2563EB'
      }
    })
    mapInstance.add(districtLayer)
    console.log('中国地图轮廓加载成功')

    const heatData = [
      {lng: 116.405285, lat: 39.904989, count: 18},
      {lng: 121.472644, lat: 31.231706, count: 22},
      {lng: 113.280637, lat: 23.125178, count: 16},
      {lng: 114.057868, lat: 22.543099, count: 19},
      {lng: 120.15507, lat: 30.274085, count: 14},
      {lng: 118.767413, lat: 32.041544, count: 12},
      {lng: 119.306239, lat: 26.075302, count: 10},
      {lng: 117.283042, lat: 31.86119, count: 11},
      {lng: 108.940175, lat: 34.341568, count: 13},
      {lng: 104.066801, lat: 30.572816, count: 15},
      {lng: 106.551557, lat: 29.563009, count: 13},
      {lng: 123.431484, lat: 41.805708, count: 9},
      {lng: 112.982279, lat: 28.19409, count: 11},
      {lng: 115.892151, lat: 28.676493, count: 10},
      {lng: 102.712251, lat: 25.040609, count: 8},
      {lng: 91.132212, lat: 29.660361, count: 4},
      {lng: 87.617733, lat: 43.792818, count: 3},
      {lng: 111.670801, lat: 40.818311, count: 7},
      {lng: 117.421901, lat: 39.418949, count: 10},
      {lng: 106.278179, lat: 38.46637, count: 6}
    ];
    
    const heatmap = new AMap.HeatMap(mapInstance, {
      radius: 30,
      opacity: [0, 0.85],
      gradient: {
        0.3: '#3B82F6',
        0.5: '#10B981',
        0.7: '#F59E0B',
        0.9: '#EF4444'
      },
      zIndex: 20
    });
    
    heatmap.setDataSet({
      data: heatData,
      max: 25
    });
    
    console.log('地图、中国轮廓和热力图加载成功！');
    
  }).catch(e => {
    console.error('地图加载失败:', e);
    mapError.value = true;
  });
};

const initCharts = () => {
  if (lineChart.value) {
    lineChartInstance = new Chart(lineChart.value, {
      type: 'line',
      data: {
        labels: matchStats.value.recent_matches.map(m => `第${m.index}次`),
        datasets: [{
          label: '匹配成功对数',
          data: matchStats.value.recent_matches.map(m => m.pairs),
          borderColor: '#1E40AF',
          backgroundColor: 'rgba(30, 64, 175, 0.1)',
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#1E40AF',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index'
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              color: '#1E293B',
              font: { size: 12 },
              padding: 15
            }
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1E40AF',
            bodyColor: '#334155',
            borderColor: '#1E40AF',
            borderWidth: 1,
            cornerRadius: 8
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: '匹配成功对数',
              color: '#475569',
              font: { size: 11 }
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.06)',
              drawBorder: false
            },
            ticks: {
              color: '#64748B',
              font: { size: 11 }
            }
          },
          x: {
            title: {
              display: true,
              text: '匹配序号',
              color: '#475569',
              font: { size: 11 }
            },
            grid: {
              display: false
            },
            ticks: {
              color: '#64748B',
              font: { size: 11 }
            }
          }
        }
      }
    })
  }

  if (radarChart.value) {
    radarChartInstance = new Chart(radarChart.value, {
      type: 'radar',
      data: {
        labels: ['外向性', '开放性', '尽责性', '宜人性', '神经质', '自恋'],
        datasets: [{
          label: '个人属性得分',
          data: [
            userPersonality.value.extraversion,
            userPersonality.value.openness,
            userPersonality.value.conscientiousness,
            userPersonality.value.agreeableness,
            userPersonality.value.neuroticism,
            userPersonality.value.narcissism
          ],
          backgroundColor: 'rgba(30, 64, 175, 0.25)',
          borderColor: '#1E40AF',
          borderWidth: 2,
          pointBackgroundColor: '#D97706',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            beginAtZero: true,
            max: 5,
            min: 0,
            ticks: {
              stepSize: 1,
              color: '#64748B',
              backdropColor: 'transparent',
              font: { size: 10 }
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.08)'
            },
            angleLines: {
              color: 'rgba(0, 0, 0, 0.08)'
            },
            pointLabels: {
              color: '#1E293B',
              font: { size: 11, weight: '600' }
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1E40AF',
            bodyColor: '#334155',
            borderColor: '#1E40AF',
            borderWidth: 1,
            cornerRadius: 8
          }
        }
      }
    })
  }

  if (pieChart.value) {
    const platformData = [
      platformPersonality.value.extraversion || 0,
      platformPersonality.value.openness || 0,
      platformPersonality.value.conscientiousness || 0,
      platformPersonality.value.agreeableness || 0,
      platformPersonality.value.neuroticism || 0
    ]
    
    pieChartInstance = new Chart(pieChart.value, {
      type: 'doughnut',
      data: {
        labels: ['外向性', '开放性', '尽责性', '宜人性', '神经质'],
        datasets: [{
          data: platformData,
          backgroundColor: [
            'rgba(30, 64, 175, 0.85)',
            'rgba(220, 38, 38, 0.85)',
            'rgba(5, 150, 105, 0.85)',
            'rgba(217, 119, 6, 0.85)',
            'rgba(139, 92, 246, 0.85)'
          ],
          borderColor: [
            '#1E40AF',
            '#DC2626',
            '#059669',
            '#D97706',
            '#8B5CF6'
          ],
          borderWidth: 2,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: '#1E293B',
              font: { size: 11 },
              padding: 15,
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1E40AF',
            bodyColor: '#334155',
            borderColor: '#1E40AF',
            borderWidth: 1,
            cornerRadius: 8,
            callbacks: {
              label: function(context) {
                return `${context.label}: ${context.parsed}`
              }
            }
          }
        }
      }
    })
  }
}

const updateCharts = () => {
  if (lineChartInstance && matchStats.value.recent_matches) {
    lineChartInstance.data.labels = matchStats.value.recent_matches.map(m => `第${m.index}次`)
    lineChartInstance.data.datasets[0].data = matchStats.value.recent_matches.map(m => m.pairs)
    lineChartInstance.update('active')
  }
  
  if (radarChartInstance) {
    radarChartInstance.data.datasets[0].data = [
      userPersonality.value.extraversion,
      userPersonality.value.openness,
      userPersonality.value.conscientiousness,
      userPersonality.value.agreeableness,
      userPersonality.value.neuroticism,
      userPersonality.value.narcissism
    ]
    radarChartInstance.update('active')
  }
  
  if (pieChartInstance) {
    const platformData = [
      platformPersonality.value.extraversion || 0,
      platformPersonality.value.openness || 0,
      platformPersonality.value.conscientiousness || 0,
      platformPersonality.value.agreeableness || 0,
      platformPersonality.value.neuroticism || 0
    ]
    pieChartInstance.data.datasets[0].data = platformData
    pieChartInstance.update('active')
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  width: 100%;
  overflow-x: hidden;
  font-family: 'Fira Sans', sans-serif;
  position: relative;
}

.background-gradient {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 35%, #10B981 65%, #8B5CF6 100%);
  z-index: -2;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.particles {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  pointer-events: none;
  overflow: hidden;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 50%;
  left: var(--x);
  top: var(--y);
  animation: floatParticle 15s ease-in-out infinite;
  animation-delay: var(--delay);
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.5), 0 0 20px rgba(255, 255, 255, 0.3);
}

@keyframes floatParticle {
  0%, 100% { transform: translateY(0) translateX(0); opacity: 0.6; }
  25% { transform: translateY(-100px) translateX(50px); opacity: 0.8; }
  50% { transform: translateY(-200px) translateX(-30px); opacity: 0.4; }
  75% { transform: translateY(-150px) translateX(-60px); opacity: 0.7; }
}

.glass-effect {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  box-shadow: 
    0 4px 24px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.glass-effect::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 16px;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(59, 130, 246, 0.2),
    transparent,
    rgba(139, 92, 246, 0.2)
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.glass-effect:hover {
  transform: translateY(-3px);
  box-shadow: 
    0 12px 36px rgba(0, 0, 0, 0.08),
    0 0 20px rgba(59, 130, 246, 0.1);
  background: rgba(255, 255, 255, 0.1);
}

.dashboard-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 14px;
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 15px;
}

.dashboard-title {
  font-size: 1.7rem;
  font-weight: 800;
  color: #0F172A;
  margin: 0;
  letter-spacing: 3px;
  text-shadow: none;
  position: relative;
  z-index: 10;
}

.dashboard-subtitle {
  font-size: 0.95rem;
  color: #475569;
  font-weight: 500;
  letter-spacing: 1px;
}

.header-center {
  flex: 1;
  text-align: center;
}

.current-time {
  font-size: 1.1rem;
  font-family: 'Fira Code', monospace;
  color: #0369A1;
  font-weight: 600;
  letter-spacing: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.auth-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-icon {
  background: rgba(30, 64, 175, 0.1);
  border: 1px solid rgba(30, 64, 175, 0.3);
  border-radius: 10px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #1E40AF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon:hover {
  background: rgba(30, 64, 175, 0.2);
  border-color: #1E40AF;
  transform: scale(1.05);
}

.btn-icon svg {
  width: 20px;
  height: 20px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
  font-family: 'Fira Sans', sans-serif;
}

.btn.primary {
  background: linear-gradient(135deg, #3B82F6, #2563EB);
  color: white;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3);
}

.btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.4);
}

.btn.secondary {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.1);
  color: #1E293B;
}

.btn.secondary:hover {
  background: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.dashboard-main {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(250px, 280px) 1fr minmax(250px, 280px);
  grid-template-rows: 1fr;
  gap: 14px;
  min-height: 600px;
  max-height: none;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  min-height: 500px;
  max-height: none;
}

@media (max-width: 1200px) {
  .dashboard-main {
    grid-template-columns: minmax(220px, 1fr) 1fr;
    grid-template-areas: 
      "left center"
      "right right";
  }
  
  .left-panel { grid-area: left; }
  .center-map-area { grid-area: center; }
  .right-panel { grid-area: right; }
}

@media (max-width: 768px) {
  .dashboard-main {
    grid-template-columns: 1fr;
    grid-template-areas: 
      "center"
      "left"
      "right";
  }
  
  .left-panel,
  .right-panel {
    max-height: 300px;
  }
}

.stat-card {
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
  border: 1px solid rgba(59, 130, 246, 0.2);
  color: #2563EB;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.stat-icon svg {
  width: 22px;
  height: 22px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: #0369A1;
  font-family: 'Fira Code', monospace;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.85rem;
  color: #475569;
  margin-top: 4px;
  font-weight: 500;
}

.chart-card {
  padding: 14px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1E293B;
  margin: 0 0 16px 0;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.title-icon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  animation: iconPulse 2s ease-in-out infinite;
}

.pulse-icon { background: #3B82F6; }
.bar-icon { background: #F59E0B; animation-delay: 0.5s; }
.pie-icon { background: #10B981; animation-delay: 1s; }

@keyframes iconPulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 8px currentColor; }
  50% { opacity: 0.5; box-shadow: 0 0 16px currentColor; }
}

.chart-wrapper {
  flex: 1;
  min-height: 280px;
  max-height: 350px;
  position: relative;
  overflow: hidden;
}

.radar-chart { 
  min-height: 320px;
  max-height: 390px;
}

.pie-chart { 
  min-height: 320px;
  max-height: 390px;
}

@media (max-width: 768px) {
  .chart-wrapper {
    min-height: 260px;
    max-height: 330px;
  }
  
  .radar-chart,
  .pie-chart {
    min-height: 280px;
    max-height: 350px;
  }
}

.center-map-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.map-card {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

.map-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #1E293B;
  margin: 0 0 10px 0;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.map-icon {
  width: 10px;
  height: 10px;
  background: radial-gradient(circle, #EF4444, #F59E0B);
  border-radius: 50%;
  animation: mapGlow 2s ease-in-out infinite;
}

@keyframes mapGlow {
  0%, 100% { box-shadow: 0 0 10px #EF4444; }
  50% { box-shadow: 0 0 20px #EF4444, 0 0 30px #F59E0B; }
}

.map-container {
  flex: 1;
  border-radius: 12px;
  overflow: hidden;
  min-height: 280px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.map-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #DC2626;
  padding: 30px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(220, 38, 38, 0.2);
  border-radius: 12px;
}

.map-error p {
  font-size: 1.1rem;
  margin: 0 0 10px 0;
  font-weight: 600;
}

.map-error small {
  font-size: 0.85rem;
  color: #64748B;
}

.features-section-hud {
  padding: 20px 16px;
  margin-top: 0;
}

.hud-container {
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.hud-corner {
  position: absolute;
  width: 30px;
  height: 30px;
  border-color: #3B82F6;
  border-style: solid;
  border-width: 0;
}

.hud-tl { top: 0; left: 0; border-top-width: 2px; border-left-width: 2px; }
.hud-tr { top: 0; right: 0; border-top-width: 2px; border-right-width: 2px; }
.hud-bl { bottom: 0; left: 0; border-bottom-width: 2px; border-left-width: 2px; }
.hud-br { bottom: 0; right: 0; border-bottom-width: 2px; border-right-width: 2px; }

.hud-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin: 0 0 16px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1E293B;
  letter-spacing: 2px;
}

.hud-text { position: relative; z-index: 1; }

.hud-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.4), transparent);
  position: relative;
}

.hud-line::after {
  content: '';
  position: absolute;
  top: -3px;
  width: 8px;
  height: 8px;
  background: #3B82F6;
  border-radius: 50%;
  left: 50%;
  transform: translateX(-50%);
}

.features-grid-hud {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.feature-card-hud {
  position: relative;
  background: rgba(255, 255, 255, 0.35);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: default;
}

.feature-card-hud:hover {
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transform: translateY(-3px);
}

.feature-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  border-radius: 50%;
  opacity: 0.08;
  filter: blur(40px);
}

.feature-icon-hud {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  border: 2px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.feature-icon-hud svg { width: 20px; height: 20px; }

.feature-card-hud:hover .feature-icon-hud {
  transform: rotateY(360deg);
  box-shadow: 0 0 20px currentColor;
}

.feature-content-hud { flex: 1; }

.feature-name-hud {
  font-size: 1rem;
  font-weight: 600;
  color: #0F172A;
  margin: 0 0 6px 0;
}

.feature-desc-hud {
  font-size: 0.82rem;
  color: #475569;
  margin: 0;
  line-height: 1.5;
}

.feature-status {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.feature-card-hud:hover .feature-status { opacity: 1; }

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: statusBlink 1s ease-in-out infinite;
}

@keyframes statusBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@media (max-width: 1400px) {
  .dashboard-main {
    grid-template-columns: 280px 1fr 280px;
  }
  .stat-value { font-size: 1.6rem; }
  .dashboard-title { font-size: 1.8rem; }
}

@media (max-width: 1200px) {
  .dashboard-main {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }
  .left-panel,
  .right-panel {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 15px;
  }
  .center-map-area { order: -1; }
  .map-container { min-height: 380px; }
  .particles { display: none; }
  .features-grid-hud { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 15px;
    gap: 15px;
  }
  .dashboard-header {
    flex-direction: column;
    gap: 12px;
    padding: 16px 20px;
  }
  .header-left,
  .header-center,
  .header-right {
    width: 100%;
    justify-content: center;
  }
  .dashboard-title { font-size: 1.5rem; }
  .current-time { font-size: 0.95rem; }
  .auth-buttons {
    width: 100%;
    justify-content: center;
  }
  .btn { padding: 10px 20px; font-size: 0.85rem; }
  .left-panel,
  .right-panel { grid-template-columns: 1fr; }
  .map-container { min-height: 300px; }
  .particle { display: none; }
  .features-grid-hud { grid-template-columns: 1fr; }
  .hud-container { padding: 20px; }
}

@media (max-width: 480px) {
  .dashboard-title { font-size: 1.3rem; }
  .current-time { font-size: 0.85rem; }
  .stat-value { font-size: 1.3rem; }
  .stat-card { padding: 16px; }
  .chart-wrapper { min-height: 160px; }
  .radar-chart { min-height: 200px; }
  .pie-chart { min-height: 170px; }
  .map-container { min-height: 250px; }
  .map-card { min-height: auto; padding: 16px; }
  .feature-card-hud { flex-wrap: wrap; }
  .feature-status { display: none; }
  .feature-desc-hud { font-size: 0.78rem; }
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #94A3B8, #CBD5E1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #64748B, #94A3B8); }
</style>

<!-- Sidebar样式：非scoped，因为Teleport到body后scoped失效 -->
<style>
.__sidebar_backdrop {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  background: rgba(0, 0, 0, 0.4) !important;
  z-index: 99998 !important;
  display: block !important;
}

.__sidebar_panel {
  position: fixed !important;
  top: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 300px !important;
  height: 100vh !important;
  z-index: 99999 !important;
  display: block !important;
  pointer-events: auto !important;
}

.__sidebar_inner {
  width: 100%;
  height: 100%;
  background: #ffffff;
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.__sidebar_header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 18px;
  border-bottom: 1px solid #f0f0f0;
  gap: 10px;
  flex-shrink: 0;
}

.__sidebar_user_info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.__user_avatar_small {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3B82F6, #8B5CF6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 700;
  flex-shrink: 0;
}

.__user_detail {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.__user_name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1E293B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.__user_email {
  font-size: 0.74rem;
  color: #94A3B8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.__close_btn {
  background: none;
  border: none;
  color: #94A3B8;
  font-size: 24px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
  line-height: 1;
}

.__close_btn:hover {
  background: #fef2f2;
  color: #DC2626;
}

.__sidebar_nav {
  flex: 1;
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.__sidebar_item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  color: #334155;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.__sidebar_item:hover {
  background: #f0f7ff;
  border-left-color: #3B82F6;
  color: #1E40AF;
  padding-left: 20px;
}

.__sidebar_divider {
  height: 1px;
  background: #f0f0f0;
  margin: 8px 14px;
}

.__logout_item {
  margin-top: 8px;
  border-top: 1px solid #f0f0f0;
  padding-top: 14px;
  color: #DC2626;
  border-left-color: transparent !important;
}

.__logout_item:hover {
  background: #fef2f2;
  border-left-color: #DC2626 !important;
  color: #DC2626;
}
</style>
