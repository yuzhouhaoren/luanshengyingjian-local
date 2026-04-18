+<template>
  <div class="dodecahedron-container">
    <canvas ref="canvas" class="dodecahedron-canvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

const canvas = ref(null)

let scene, camera, renderer, dodecahedron, edges, points, energyParticles
let animationId = null
let time = 0

const initThreeJS = () => {
  // 创建场景
  scene = new THREE.Scene()
  scene.background = null // 设置为透明背景
  
  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ 
    canvas: canvas.value,
    antialias: true,
    alpha: true
  })
  
  // 设置渲染器尺寸为容器尺寸
  const container = canvas.value.parentElement
  const width = container.clientWidth
  const height = container.clientHeight
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  
  // 创建相机（设置正确的宽高比）
  camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
  camera.position.z = 4 // 相机更远，图形更完整
  
  // 使用Three.js内置的正十二面体几何体（增大到原来的2倍）
  const geometry = new THREE.DodecahedronGeometry(2, 0)
  
  // 移除面片材质，只显示点和边
  
  // 创建蓝色边线（背后模糊效果）
  const edgesGeometry = new THREE.EdgesGeometry(geometry)
  const edgesMaterial = new THREE.LineBasicMaterial({ 
    color: 0x4169E1, // 蓝色
    linewidth: 2,
    transparent: true,
    opacity: 0.8
  })
  edges = new THREE.LineSegments(edgesGeometry, edgesMaterial)
  scene.add(edges)
  
  // 创建蓝色顶点球体（真正的圆形球体）
  const vertices = geometry.attributes.position.array
  
  // 为每个顶点创建一个球体
  const sphereGeometry = new THREE.SphereGeometry(0.04, 16, 16) // 球体半径0.15，16x16细分
  const sphereMaterial = new THREE.MeshBasicMaterial({
    color: 0x4169E1, // 蓝色
    transparent: true,
    opacity: 0.9
  })
  
  // 创建球体组
  const sphereGroup = new THREE.Group()
  
  // 为每个顶点位置创建一个球体
  for (let i = 0; i < vertices.length; i += 3) {
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial)
    sphere.position.set(vertices[i], vertices[i + 1], vertices[i + 2])
    sphereGroup.add(sphere)
  }
  
  points = sphereGroup
  scene.add(points)
  
  // 添加柔和的环境光
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.3)
  scene.add(ambientLight)
  
  // 创建能量流动效果
  createEnergyFlow()
  
  // 开始动画
  animate()
}

const createEnergyFlow = () => {
  // 获取正十二面体的边信息
  const geometry = new THREE.DodecahedronGeometry(2, 0)
  const edgesGeometry = new THREE.EdgesGeometry(geometry)
  
  // 创建能量粒子系统
  const particleCount = 60 // 粒子数量
  const positions = new Float32Array(particleCount * 3)
  const colors = new Float32Array(particleCount * 3)
  
  // 初始化粒子位置和颜色
  for (let i = 0; i < particleCount; i++) {
    const index = i * 3
    // 随机分布在正十二面体表面
    positions[index] = (Math.random() - 0.5) * 4
    positions[index + 1] = (Math.random() - 0.5) * 4
    positions[index + 2] = (Math.random() - 0.5) * 4
    
    // 蓝色到白色的渐变颜色
    colors[index] = 0.2 + Math.random() * 0.8 // R
    colors[index + 1] = 0.4 + Math.random() * 0.6 // G
    colors[index + 2] = 1.0 // B
  }
  
  const particleGeometry = new THREE.BufferGeometry()
  particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  
  const particleMaterial = new THREE.PointsMaterial({
    size: 0.08,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending
  })
  
  energyParticles = new THREE.Points(particleGeometry, particleMaterial)
  scene.add(energyParticles)
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  time += 0.02
  
  // 旋转动画
  if (edges) {
    // 绕Y轴旋转
    edges.rotation.y += 0.01
    // 绕X轴轻微旋转，增加立体感
    edges.rotation.x += 0.005
  }
  
  if (points) {
    points.rotation.y += 0.01
    points.rotation.x += 0.005
  }
  
  // 能量粒子流动效果
  if (energyParticles) {
    const positions = energyParticles.geometry.attributes.position.array
    const colors = energyParticles.geometry.attributes.color.array
    
    for (let i = 0; i < positions.length; i += 3) {
      const particleIndex = i / 3
      
      // 粒子沿着正十二面体表面移动
      const angle = time + particleIndex * 0.1
      const radius = 2 + Math.sin(angle) * 0.1
      
      // 球面坐标移动
      positions[i] = radius * Math.sin(angle) * Math.cos(particleIndex * 0.5)
      positions[i + 1] = radius * Math.sin(angle) * Math.sin(particleIndex * 0.5)
      positions[i + 2] = radius * Math.cos(angle)
      
      // 颜色脉冲效果
      const pulse = Math.sin(time * 2 + particleIndex * 0.2) * 0.5 + 0.5
      colors[i] = 0.2 + pulse * 0.6 // R
      colors[i + 1] = 0.4 + pulse * 0.4 // G
      colors[i + 2] = 0.8 + pulse * 0.2 // B
    }
    
    energyParticles.geometry.attributes.position.needsUpdate = true
    energyParticles.geometry.attributes.color.needsUpdate = true
    energyParticles.rotation.y += 0.005
  }
  
  renderer.render(scene, camera)
}

const cleanup = () => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  
  if (renderer) {
    renderer.dispose()
  }
  
  if (scene) {
    scene.traverse((object) => {
      if (object.geometry) {
        object.geometry.dispose()
      }
      if (object.material) {
        if (Array.isArray(object.material)) {
          object.material.forEach(material => material.dispose())
        } else {
          object.material.dispose()
        }
      }
    })
  }
}

const handleResize = () => {
  if (renderer && canvas.value) {
    const container = canvas.value.parentElement
    const width = container.clientWidth
    const height = container.clientHeight
    
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    renderer.setSize(width, height)
  }
}

onMounted(() => {
  if (canvas.value) {
    initThreeJS()
    window.addEventListener('resize', handleResize)
  }
})

onUnmounted(() => {
  cleanup()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dodecahedron-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 50vh; /* 只占据视口高度的50%，避免被glass-card遮挡 */
  z-index: 1;
  pointer-events: none;
}

.dodecahedron-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dodecahedron-container {
    height: 200px;
  }
}

@media (max-width: 480px) {
  .dodecahedron-container {
    height: 150px;
  }
}
</style>