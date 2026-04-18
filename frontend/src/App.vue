<template>
  <div class="app">
    <!-- 动态背景 -->
    <canvas ref="bgCanvas" class="bg-canvas"></canvas>

    <!-- 导航栏 -->
    <nav class="navbar" :class="{ 'navbar-hidden': !isNavbarVisible }">
      <div class="container">
        <router-link to="/" class="navbar-logo">孪生映见</router-link>

        <!-- 移动端菜单按钮 -->
        <div
          class="mobile-menu-toggle"
          @click="toggleMobileMenu"
          :class="{ active: mobileMenuOpen }"
        >
          <div class="menu-icon">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>

        <ul class="navbar-links">
          <li>
            <router-link to="/" :class="{ active: currentRoute === '/' }"
              >首页</router-link
            >
          </li>
          <li class="nav-divider"></li>
          <li>
            <router-link
              to="/profile"
              :class="{ active: currentRoute === '/profile' }"
              >个人画像</router-link
            >
          </li>
          <li>
            <router-link
              to="/intent"
              :class="{ active: currentRoute === '/intent' }"
              >匹配意向</router-link
            >
          </li>
          <li class="nav-divider"></li>
          <li>
            <router-link
              to="/match-pool"
              :class="{ active: currentRoute === '/match-pool' }"
              class="nav-special"
            >
              匹配池
              <span v-if="notificationCount > 0" class="notification-badge">{{
                notificationCount
              }}</span>
            </router-link>
          </li>
          <li>
            <router-link
              to="/square"
              :class="{ active: currentRoute === '/square' }"
              class="nav-special"
              >聊天广场</router-link
            >
          </li>
          <li v-if="!user">
            <router-link
              to="/login"
              :class="{ active: currentRoute === '/login' }"
              >登录</router-link
            >
          </li>
          <li v-if="!user">
            <router-link
              to="/register"
              :class="{ active: currentRoute === '/register' }"
              >注册</router-link
            >
          </li>
          <li v-if="user" class="user-profile">
            <div class="user-avatar" @click="toggleSidebar">
              <img :src="userAvatar" alt="用户头像" class="avatar-img" />
              <span v-if="notificationCount > 0" class="avatar-badge">{{
                notificationCount
              }}</span>
            </div>
            <button @click="logout" class="logout-btn">退出登录</button>
          </li>
        </ul>
      </div>
    </nav>

    <!-- 移动端菜单 -->
    <div class="mobile-menu" :class="{ open: mobileMenuOpen }">
      <div class="mobile-menu-content">
        <div class="mobile-menu-header">
          <h3>导航菜单</h3>
          <div class="mobile-menu-close" @click="toggleMobileMenu">✕</div>
        </div>
        <ul class="mobile-menu-links">
          <li>
            <router-link
              to="/"
              @click="toggleMobileMenu"
              :class="{ active: currentRoute === '/' }"
              >首页</router-link
            >
          </li>
          <li>
            <router-link
              to="/profile"
              @click="toggleMobileMenu"
              :class="{ active: currentRoute === '/profile' }"
              >个人画像</router-link
            >
          </li>
          <li>
            <router-link
              to="/intent"
              @click="toggleMobileMenu"
              :class="{ active: currentRoute === '/intent' }"
              >匹配意向</router-link
            >
          </li>
          <li>
            <router-link
              to="/match-pool"
              @click="toggleMobileMenu"
              :class="{ active: currentRoute === '/match-pool' }"
            >
              匹配池
              <span v-if="notificationCount > 0" class="notification-badge">{{
                notificationCount
              }}</span>
            </router-link>
          </li>
          <li>
            <router-link
              to="/square"
              @click="toggleMobileMenu"
              :class="{ active: currentRoute === '/square' }"
              >聊天广场</router-link
            >
          </li>
          <li v-if="!user">
            <router-link
              to="/login"
              @click="toggleMobileMenu"
              :class="{ active: currentRoute === '/login' }"
              >登录</router-link
            >
          </li>
          <li v-if="!user">
            <router-link
              to="/register"
              @click="toggleMobileMenu"
              :class="{ active: currentRoute === '/register' }"
              >注册</router-link
            >
          </li>
          <li v-if="user" class="mobile-user-profile">
            <div class="mobile-user-info" @click="toggleSidebar">
              <img :src="userAvatar" alt="用户头像" class="avatar-img" />
              <span class="user-name">{{ user.username }}</span>
              <span v-if="notificationCount > 0" class="avatar-badge">{{
                notificationCount
              }}</span>
            </div>
            <button @click="logout" class="mobile-logout-btn">退出登录</button>
          </li>
        </ul>
      </div>
    </div>

    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-toggle" @click="toggleSidebar">
        <div class="toggle-icon">
          <div class="triangle-container" :class="{ open: sidebarOpen }">
            <svg viewBox="0 0 20 17">
              <path class="triangle-path" d="M10 1 L19 16 L1 16 Z" />
              <circle class="triangle-dot" cx="10" cy="1" r="3" />
              <circle class="triangle-dot" cx="19" cy="16" r="3" />
              <circle class="triangle-dot" cx="1" cy="16" r="3" />
            </svg>
          </div>
        </div>
      </div>
      <div class="sidebar-content">
        <div class="sidebar-header">
          <h3>个人中心</h3>
        </div>
        <div class="sidebar-links">
          <router-link
            to="/settings"
            class="sidebar-link"
            @click="toggleSidebar"
          >
            <span class="link-icon">⚙️</span>
            <span>设置</span>
          </router-link>
          <router-link to="/user" class="sidebar-link" @click="toggleSidebar">
            <span class="link-icon">👤</span>
            <span>个人主页</span>
            <span v-if="notificationCount > 0" class="sidebar-badge">{{
              notificationCount
            }}</span>
          </router-link>
        </div>
      </div>
    </div>

    <!-- 主内容 -->
    <main class="main-content" :class="{ 'sidebar-open': sidebarOpen }">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="container">
        <p>&copy; 2026 孪生映见. 保留所有权利.</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import axios from "axios";

// 根据性别获取默认头像
const getDefaultAvatar = (gender) => {
  if (gender === '男') {
    return 'http://localhost:5000/avatars/男.jpg'
  } else {
    return 'http://localhost:5000/avatars/女.jpg'
  }
}

const router = useRouter();
const route = useRoute();
const user = ref(null);
const userAvatar = ref(getDefaultAvatar('男'));
const bgCanvas = ref(null);
const sidebarOpen = ref(false);
const mobileMenuOpen = ref(false);
const notificationCount = ref(0);
const isNavbarVisible = ref(true);

// 计算当前路由
const currentRoute = computed(() => {
  return route.path;
});

// 动态背景相关变量
let animationId = null;
let points = [];
let mousePoint = {
  x: 0,
  y: 0,
  radius: 3,
  opacity: 0.5,
  opacityDirection: 1,
  opacitySpeed: 0.01,
};
const canvasWidth = window.innerWidth;
const canvasHeight = window.innerHeight;
const pointCount = 60;
const maxDistance = 180;
const colors = ["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE"];

let lastScrollPosition = 0;

// 处理滚动
const handleScroll = () => {
  if (window.scrollY > lastScrollPosition && window.scrollY > 50) {
    isNavbarVisible.value = false;
  } else {
    isNavbarVisible.value = true;
  }
  lastScrollPosition = window.scrollY;
};

// 检查用户状态
const checkUserStatus = async () => {
  const savedUser = localStorage.getItem("user");
  if (savedUser) {
    user.value = JSON.parse(savedUser);
    // 获取用户头像
    await fetchUserAvatar(user.value.id);
    // 获取通知数量
    await fetchNotificationCount(user.value.id);
  } else {
    user.value = null;
    userAvatar.value = getDefaultAvatar('男');
    notificationCount.value = 0;
  }
};

// 获取通知数量
const fetchNotificationCount = async (userId) => {
  try {
    const response = await axios.get(
      `http://localhost:5000/api/notifications/${userId}`,
    );
    if (response.data.status === "success") {
      notificationCount.value = response.data.data.total;
    }
  } catch (error) {
    console.error("获取通知数量失败:", error);
    notificationCount.value = 0;
  }
};

// 获取用户头像
const fetchUserAvatar = async (userId) => {
  // 优先使用localStorage中的头像（如果存在）
  const savedUser = localStorage.getItem("user");
  if (savedUser) {
    const userObj = JSON.parse(savedUser);
    if (userObj.avatar) {
      userAvatar.value = userObj.avatar;
      return;
    }
  }

  try {
    const response = await axios.get(
      `http://localhost:5000/api/profile/${userId}`,
    );
    if (response.data.status === "success" && response.data.profile) {
      const profile = response.data.profile;
      if (profile.avatar) {
        userAvatar.value = `http://localhost:5000/avatars/${profile.avatar}`;
      } else {
        userAvatar.value = getDefaultAvatar(profile.gender || '男');
      }
    }
  } catch (error) {
    console.error("获取用户头像失败:", error);
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      const userObj = JSON.parse(savedUser);
      userAvatar.value = getDefaultAvatar(userObj.gender || '男');
    } else {
      userAvatar.value = getDefaultAvatar('男');
    }
  }
};

// 初始化背景
const initBackground = () => {
  const canvas = bgCanvas.value;
  if (!canvas) return;

  canvas.width = canvasWidth;
  canvas.height = canvasHeight;

  // 创建随机点
  points = [];
  for (let i = 0; i < pointCount; i++) {
    const color = colors[Math.floor(Math.random() * colors.length)];
    points.push({
      x: Math.random() * canvasWidth,
      y: Math.random() * canvasHeight,
      radius: 2 + Math.random() * 2,
      dx: (Math.random() - 0.5) * 0.5,
      dy: (Math.random() - 0.5) * 0.5,
      color: color,
    });
  }

  // 监听鼠标移动
  window.addEventListener("mousemove", handleMouseMove);

  // 开始动画
  animate();
};

// 处理鼠标移动
const handleMouseMove = (event) => {
  mousePoint.x = event.clientX;
  mousePoint.y = event.clientY;
};

// 动画函数
const animate = () => {
  const canvas = bgCanvas.value;
  if (!canvas) return;

  const ctx = canvas.getContext("2d");

  // 清空画布
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  // 更新点的位置
  points.forEach((point) => {
    point.x += point.dx;
    point.y += point.dy;

    // 边界检测
    if (point.x < 0 || point.x > canvasWidth) point.dx *= -1;
    if (point.y < 0 || point.y > canvasHeight) point.dy *= -1;
  });

  // 绘制点和连线
  points.forEach((point) => {
    // 添加点的脉动效果
    const pulseRadius =
      point.radius + Math.sin(Date.now() * 0.001 + point.x * 0.001) * 0.5;

    // 绘制点的外层光晕
    ctx.beginPath();
    ctx.arc(point.x, point.y, pulseRadius * 2, 0, Math.PI * 2);
    ctx.fillStyle = `${point.color}20`; // 20是透明度，十六进制
    ctx.fill();

    // 绘制点
    ctx.beginPath();
    ctx.arc(point.x, point.y, point.radius, 0, Math.PI * 2);
    ctx.fillStyle = point.color;
    ctx.fill();

    // 绘制与其他点的连线
    points.forEach((otherPoint) => {
      const distance = getDistance(point, otherPoint);
      if (distance < maxDistance) {
        // 计算连线的透明度和宽度
        const opacity = 0.3 * (1 - distance / maxDistance);
        const width = 0.3 + (1 - distance / maxDistance) * 0.7;

        // 绘制渐变连线
        const gradient = ctx.createLinearGradient(
          point.x,
          point.y,
          otherPoint.x,
          otherPoint.y,
        );
        gradient.addColorStop(0, point.color);
        gradient.addColorStop(1, otherPoint.color);

        ctx.beginPath();
        ctx.moveTo(point.x, point.y);
        ctx.lineTo(otherPoint.x, otherPoint.y);
        ctx.strokeStyle = gradient;
        ctx.globalAlpha = opacity;
        ctx.lineWidth = width;
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
    });

    // 绘制与鼠标点的连线
    const mouseDistance = getDistance(point, mousePoint);
    if (mouseDistance < maxDistance) {
      const opacity = 0.4 * (1 - mouseDistance / maxDistance);
      const width = 0.5 + (1 - mouseDistance / maxDistance) * 1;

      ctx.beginPath();
      ctx.moveTo(point.x, point.y);
      ctx.lineTo(mousePoint.x, mousePoint.y);
      ctx.strokeStyle = point.color;
      ctx.globalAlpha = opacity;
      ctx.lineWidth = width;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
  });

  // 更新鼠标点的呼吸灯效果
  mousePoint.opacity += mousePoint.opacityDirection * mousePoint.opacitySpeed;
  if (mousePoint.opacity >= 1) {
    mousePoint.opacityDirection = -1;
  } else if (mousePoint.opacity <= 0.2) {
    mousePoint.opacityDirection = 1;
  }

  // 绘制鼠标点的外层光晕
  ctx.beginPath();
  ctx.arc(mousePoint.x, mousePoint.y, mousePoint.radius * 3, 0, Math.PI * 2);
  ctx.fillStyle = `rgba(37, 99, 235, ${mousePoint.opacity * 0.3})`;
  ctx.fill();

  // 绘制鼠标点
  ctx.beginPath();
  ctx.arc(mousePoint.x, mousePoint.y, mousePoint.radius, 0, Math.PI * 2);
  ctx.fillStyle = `rgba(37, 99, 235, ${mousePoint.opacity})`;
  ctx.fill();

  // 继续动画
  animationId = requestAnimationFrame(animate);
};

// 计算两点之间的距离
const getDistance = (p1, p2) => {
  const dx = p1.x - p2.x;
  const dy = p1.y - p2.y;
  return Math.sqrt(dx * dx + dy * dy);
};

onMounted(() => {
  checkUserStatus();
  initBackground();

  // 监听头像更新事件
  window.addEventListener("avatar-updated", (event) => {
    userAvatar.value = event.detail.avatar;
  });
  window.addEventListener("scroll", handleScroll);
});

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId);
  }
  window.removeEventListener("mousemove", handleMouseMove);
  window.removeEventListener("avatar-updated", () => {});
  window.removeEventListener("scroll", handleScroll);
});

// 监听路由变化，检查用户状态
watch(
  () => route.path,
  (newPath) => {
    checkUserStatus();

    // 检查用户是否要访问需要登录的页面
    if (
      (newPath === "/profile" ||
        newPath === "/intent" ||
        newPath === "/square" ||
        newPath === "/match-pool") &&
      !localStorage.getItem("user")
    ) {
      alert("请先登录，然后再访问该页面");
      router.push("/login");
    }

    // 检查用户是否要访问匹配池页面，需要有个人画像和匹配意向
    if (
      newPath === "/match-pool" &&
      !localStorage.getItem("intent_completed")
    ) {
      alert("请先完成个人画像和匹配意向，然后再访问匹配池");
      router.push("/profile");
    }
  },
);

const logout = () => {
  localStorage.removeItem("user");
  localStorage.removeItem("intent_completed");
  user.value = null;
  router.push("/");
};

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value;
  // 防止菜单打开时可以滚动页面
  if (mobileMenuOpen.value) {
    document.body.style.overflow = "hidden";
  } else {
    document.body.style.overflow = "auto";
  }
};

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};

const confirmDeleteAccount = async () => {
  if (confirm("确定要注销账号吗？此操作不可恢复。")) {
    try {
      const user = JSON.parse(localStorage.getItem("user"));
      if (user) {
        // 调用后端API注销账号
        const response = await axios.post(
          "http://localhost:5000/api/account/delete",
          {
            user_id: user.id,
          },
        );

        if (response.data.status === "success") {
          localStorage.removeItem("user");
          localStorage.removeItem("intent_completed");
          user.value = null;
          sidebarOpen.value = false;
          router.push("/login");
          alert("账号已成功注销");
        } else {
          alert("注销账号失败: " + (response.data.message || "未知错误"));
        }
      }
    } catch (error) {
      console.error("注销账号失败:", error);
      alert("注销账号失败，请稍后重试");
    }
  }
};
</script>

<style scoped>
.app {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.bg-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.navbar {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 1200px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transition: all 0.3s ease;
}

.navbar.navbar-hidden {
  transform: translate(-50%, -150%);
}

.navbar:hover {
  background: rgba(255, 255, 255, 0.3);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.navbar .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
}

.navbar-logo {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.navbar-logo:hover {
  color: #1d4ed8;
  transform: scale(1.05);
}

.navbar-links {
  display: flex;
  gap: 20px;
  list-style: none;
  align-items: center;
}

.nav-divider {
  width: 1px;
  height: 30px;
  background: #2563eb;
  margin: 0 10px;
}

.nav-special {
  font-family: "Arial", sans-serif;
  font-weight: 600;
  color: #2563eb !important;
}

.navbar-links a {
  text-decoration: none;
  color: #1e293b;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
  padding: 8px 16px;
  border-radius: 8px;
}

.navbar-links a:hover {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.1);
}

.navbar-links a.active {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.1);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

.notification-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #ef4444;
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
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.logout-btn {
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 10px;
}

.logout-btn:hover {
  background: rgba(249, 115, 22, 0.2);
  transform: translateY(-2px);
}

/* 用户头像样式 */
.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
}

.user-avatar:hover {
  transform: scale(1.1);
}

.avatar-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.avatar-img:hover {
  border-color: #2563eb;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.main-content {
  padding-top: 120px;
  padding-bottom: 60px;
  min-height: 100vh;
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.footer {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  padding: 30px 0;
  text-align: center;
  color: #475569;
  margin-top: 60px;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease-in-out;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* 移动端菜单按钮 */
.mobile-menu-toggle {
  display: none;
  cursor: pointer;
  z-index: 101;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.mobile-menu-toggle:hover {
  background: rgba(37, 99, 235, 0.1);
}

.mobile-menu-toggle.active {
  background: rgba(37, 99, 235, 0.1);
}

.menu-icon {
  width: 24px;
  height: 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.3s ease;
}

.menu-icon span {
  display: block;
  width: 100%;
  height: 2px;
  background: #2563eb;
  border-radius: 3px;
  transition: all 0.3s ease;
  transform-origin: center;
}

/* 汉堡菜单动画 */
.mobile-menu-toggle.active .menu-icon span:nth-child(1) {
  transform: rotate(45deg) translate(4px, 4px);
}

.mobile-menu-toggle.active .menu-icon span:nth-child(2) {
  opacity: 0;
}

.mobile-menu-toggle.active .menu-icon span:nth-child(3) {
  transform: rotate(-45deg) translate(4px, -4px);
}

/* 头像徽章样式 */
.avatar-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #ef4444;
  color: white;
  font-size: 12px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  animation: pulse 2s infinite;
  border: 2px solid rgba(255, 255, 255, 0.9);
}

/* 移动端菜单 */
.mobile-menu {
  position: fixed;
  top: 0;
  right: -100%;
  width: 80%;
  height: 100vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  z-index: 100;
  transition: right 0.3s ease;
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.1);
}

.mobile-menu.open {
  right: 0;
}

.mobile-menu-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.mobile-menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid rgba(37, 99, 235, 0.2);
}

.mobile-menu-header h3 {
  margin: 0;
  color: #2563eb;
  font-size: 1.2rem;
}

.mobile-menu-close {
  font-size: 1.5rem;
  cursor: pointer;
  color: #1e293b;
  transition: all 0.3s ease;
}

.mobile-menu-close:hover {
  color: #2563eb;
  transform: rotate(90deg);
}

.mobile-menu-links {
  flex: 1;
  list-style: none;
  padding: 20px;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mobile-menu-links li {
  margin: 0;
}

.mobile-menu-links a {
  display: block;
  padding: 15px;
  color: #1e293b;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
}

.mobile-menu-links a:hover {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.1);
  transform: translateX(5px);
}

.mobile-menu-links a.active {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.1);
  font-weight: 600;
}

.mobile-user-profile {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid rgba(37, 99, 235, 0.2);
}

.mobile-user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.mobile-user-info:hover {
  background: rgba(37, 99, 235, 0.1);
}

.mobile-user-info .avatar-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.user-name {
  font-weight: 500;
  color: #1e293b;
}

.mobile-logout-btn {
  width: 100%;
  padding: 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  margin-top: 10px;
}

.mobile-logout-btn:hover {
  background: #dc2626;
}

/* 响应式设计 */
@media (max-width: 992px) {
  .navbar-links a {
    font-size: 14px;
    padding: 8px 12px;
  }
}

@media (max-width: 868px) {
  .navbar {
    width: 95%;
    top: 10px;
  }

  .navbar .container {
    padding: 10px 16px;
  }

  .navbar-logo {
    font-size: 1.2rem;
  }

  .navbar-links {
    display: none;
  }

  .mobile-menu-toggle {
    display: block;
  }

  .main-content {
    padding-top: 90px;
  }

  /* 移动端侧边栏调整 */
  .sidebar {
    width: 100%;
    height: 100vh;
    right: -100%;
    top: 0;
    transform: none;
    border-radius: 0;
  }

  .sidebar.open {
    right: 0;
  }

  .sidebar-toggle {
    display: none;
  }

  .main-content.sidebar-open {
    margin-right: 0;
  }

  .sidebar-content {
    padding: 30px 20px;
  }

  .sidebar-link {
    padding: 15px 16px;
    font-size: 16px;
  }

  .link-icon {
    font-size: 18px;
  }
}

@media (max-width: 480px) {
  .navbar {
    width: 95%;
    top: 10px;
  }

  .navbar .container {
    padding: 8px 12px;
  }

  .navbar-logo {
    font-size: 1.1rem;
  }

  .mobile-menu {
    width: 100%;
  }

  .main-content {
    padding-top: 80px;
  }

  .mobile-menu-links a {
    padding: 12px 15px;
    font-size: 16px;
  }

  .mobile-user-info {
    padding: 12px 15px;
  }

  .mobile-logout-btn {
    padding: 10px 12px;
  }
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(1.05);
}

/* 导航栏链接的动画效果 */
.navbar-links a {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 卡片悬停效果增强 */
.glass-card {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

/* 按钮动画效果 */
.btn {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 输入框聚焦动画 */
input:focus,
select:focus,
textarea:focus {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 侧边栏样式 */
.sidebar {
  position: fixed;
  top: 50%;
  right: -250px;
  transform: translateY(-50%);
  width: 250px;
  height: 300px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(37, 99, 235, 0.3);
  border-radius: 12px 0 0 12px;
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 999;
  display: flex;
}

.sidebar.open {
  right: 0;
}

.sidebar-toggle {
  position: absolute;
  left: -40px;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(37, 99, 235, 0.3);
  border-radius: 12px 0 0 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-50%) scale(1.05);
}

.toggle-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.triangle-container {
  width: 20px;
  height: 17px;
  position: relative;
}

.triangle-container svg {
  width: 100%;
  height: 100%;
  transform-origin: center;
  animation: triangleRotate 3s infinite ease-in-out;
}

.triangle-container.open svg {
  animation: triangleRotateOpen 3s infinite ease-in-out;
}

/* 三角形路径 */
.triangle-path {
  fill: none;
  stroke: #2563eb;
  stroke-width: 2;
  stroke-dasharray: 53;
  stroke-dashoffset: 0;
  animation: triangleDraw 3s infinite ease-in-out;
}

.triangle-dot {
  fill: #2563eb;
  opacity: 0;
  animation: dotAppear 3s infinite ease-in-out;
}

/* 正常状态动画 */
@keyframes triangleRotate {
  0% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(60deg);
  }
  100% {
    transform: rotate(0deg);
  }
}

@keyframes triangleDraw {
  0%,
  10% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
  30% {
    stroke-dashoffset: 53;
    opacity: 0;
  }
  40% {
    opacity: 0;
  }
  60% {
    opacity: 0;
  }
  70% {
    stroke-dashoffset: 53;
    opacity: 0;
  }
  90%,
  100% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
}

@keyframes dotAppear {
  0%,
  30%,
  70%,
  100% {
    opacity: 0;
  }
  40%,
  60% {
    opacity: 1;
  }
}

/* 打开状态动画 */
@keyframes triangleRotateOpen {
  0% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(-60deg);
  }
  100% {
    transform: rotate(0deg);
  }
}

.triangle-container.open .triangle-path {
  animation: triangleDrawOpen 3s infinite ease-in-out;
}

.triangle-container.open .triangle-dot {
  animation: dotAppearOpen 3s infinite ease-in-out;
}

@keyframes triangleDrawOpen {
  0%,
  10% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
  30% {
    stroke-dashoffset: 60;
    opacity: 0;
  }
  40% {
    opacity: 0;
  }
  60% {
    opacity: 0;
  }
  70% {
    stroke-dashoffset: 60;
    opacity: 0;
  }
  90%,
  100% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
}

@keyframes dotAppearOpen {
  0%,
  30%,
  70%,
  100% {
    opacity: 0;
  }
  40%,
  60% {
    opacity: 1;
  }
}

.sidebar-content {
  width: 100%;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  margin-bottom: 20px;
  text-align: center;
}

.sidebar-header h3 {
  color: #1e293b;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.sidebar-links {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: #1e293b;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.sidebar-link:hover {
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  transform: translateX(-5px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.sidebar-badge {
  margin-left: auto;
  background: #ef4444;
  color: white;
  font-size: 11px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  animation: pulse 2s infinite;
}

.link-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
}

/* 主内容区域调整 */
.main-content.sidebar-open {
  margin-right: 250px;
}

/* 移动端菜单增强 */
.mobile-menu-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(10px);
}

.mobile-menu-links {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.mobile-menu-links li {
  margin-bottom: 8px;
}

.mobile-menu-links a {
  display: block;
  padding: 15px 20px;
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.mobile-menu-links a::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(37, 99, 235, 0.1),
    transparent
  );
  transition: left 0.5s ease;
}

.mobile-menu-links a:hover::before {
  left: 100%;
}

.mobile-menu-links a.active {
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

.mobile-user-profile {
  margin-top: auto;
  padding: 20px;
  border-top: 1px solid rgba(37, 99, 235, 0.2);
  background: rgba(255, 255, 255, 0.9);
}

.mobile-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 20px;
  border-radius: 10px;
  transition: all 0.3s ease;
  position: relative;
  cursor: pointer;
}

.mobile-user-info:hover {
  background: rgba(37, 99, 235, 0.1);
  transform: translateY(-2px);
}

.mobile-logout-btn {
  width: 100%;
  padding: 14px 20px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  margin-top: 12px;
  font-size: 16px;
}

.mobile-logout-btn:hover {
  background: #dc2626;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

/* 移动端触摸反馈 */
@media (hover: none) and (pointer: coarse) {
  .mobile-menu-links a {
    touch-action: manipulation;
  }

  .mobile-menu-links a:active {
    transform: scale(0.98);
  }

  .mobile-logout-btn:active {
    transform: scale(0.98);
  }

  .mobile-user-info:active {
    transform: scale(0.98);
  }

  .mobile-menu-toggle:active {
    transform: scale(0.98);
  }

  .user-avatar:active {
    transform: scale(0.95);
  }

  .logout-btn:active {
    transform: scale(0.95);
  }
}
</style>
