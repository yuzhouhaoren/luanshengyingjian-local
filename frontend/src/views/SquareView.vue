<template>
  <div class="square-container">
    <!-- 意向确认组件 -->
    <div v-if="showIntentConfirm" class="intent-confirm-container">
      <div class="intent-confirm-content">
        <h3>选择匹配意向</h3>
        <p>您有多个匹配意向，请选择一个进入聊天广场：</p>
        <div class="intent-options">
          <div class="intent-option" v-for="(intent, index) in userIntents" :key="intent.intent_type" @click="selectIntent(index + 1)">
            <div class="intent-icon">{{ index === 0 ? '❤️' : '🤝' }}</div>
            <span>{{ intent.intent_type }}</span>
          </div>
        </div>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="cancel">取消</button>
        </div>
      </div>
    </div>
    
    <!-- 广场帖子 -->
    <div v-else-if="intentConfirmed" class="glass-card">
      <div class="square-header">
        <h1>聊天广场</h1>
        <div class="current-intent">
          <span>当前意向：{{ currentIntent }}</span>
          <button class="btn-switch-intent" @click="switchIntent">切换意向</button>
        </div>
      </div>
      
      <div class="posts-section">
        <h2>广场动态</h2>
        <div class="posts-grid">
          <div class="post-card" v-for="user in users" :key="user.id">
            <div class="post-header">
              <div class="post-author">
                <img :src="getUserAvatar(user)" alt="头像" class="author-avatar">
                <div class="author-info">
                  <span class="author-name">{{ user.name || user.username }}</span>
                  <span class="gender-symbol">{{ user.gender === '男' ? '♂' :( user.gender === '女' ? '♀':'' ) }}</span>
                </div>
              </div>
            </div>
            <div class="post-content">
              <h3>{{ user.name || user.username }}的个人帖子</h3>
              <p>{{ user.post_content || '点击查看详情并开始聊天' }}</p>
              <img v-if="user.post_image" :src="user.post_image" alt="帖子图片" class="post-image">
            </div>
            <div class="post-footer">
              <button class="post-action" @click="openChatDialog(user)">和Ta聊聊</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 聊天对话框 -->
    <div class="chat-dialog" v-if="selectedBot">
      <div class="chat-dialog-content">
        <div class="chat-dialog-header">
          <h3>{{ selectedBot.name }}</h3>
          <button class="close-btn" @click="closeChatDialog">&times;</button>
        </div>
        <div class="chat-dialog-messages">
          <div class="message" :class="{ 'bot-message': !msg.isUser, 'user-message': msg.isUser }" v-for="(msg, index) in messages" :key="index">
            <div class="message-content">{{ msg.content }}</div>
          </div>
        </div>
        <div class="chat-dialog-input">
          <input type="text" v-model="messageInput" @keyup.enter="sendMessage" placeholder="输入消息...">
          <button @click="sendMessage">发送</button>
        </div>
        <div class="chat-dialog-footer">
          
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const users = ref([]);
const selectedBot = ref(null);
const messages = ref([]);
const messageInput = ref('');
const showIntentConfirm = ref(false);
const userIntents = ref([]);
const intentConfirmed = ref(false);
const currentIntent = ref('');

// 初始化当前意向
const initCurrentIntent = () => {
  currentIntent.value = localStorage.getItem('current_intent') || '';
};

onMounted(async () => {
  // 检查用户的匹配意向
  await checkUserIntent();
});

const checkUserIntent = async () => {
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user) {
    alert('请先登录，然后再访问聊天广场');
    router.push('/login');
    return;
  }
  
  try {
    // 检查用户的个人画像是否完成
    const profileResponse = await axios.get(`http://localhost:5000/api/profile/${user.id}`);
    if (profileResponse.data.status === 'success' && profileResponse.data.profile) {
      const profile = profileResponse.data.profile;
      // 检查个人画像是否完成
      if (!profile.age || !profile.gender || !profile.occupation || !profile.sexual_orientation ) {
        alert('请先完成个人画像的填写，然后再访问聊天广场');
        router.push('/profile');
        return;
      }
    }
    
    // 检查用户的匹配意向
    const response = await axios.get('http://localhost:5000/api/intent/' + user.id);
    if (response.data.status === 'success') {
      const intents = response.data.data.intents;
      if (intents.length === 0) {
        // 没有填写意向，重定向到意向页面
        alert('请先完成匹配意向的填写，然后再访问聊天广场');
        router.push('/intent');
      } else if (intents.length > 1) {
        // 有多个意向，显示意向确认组件
        userIntents.value = intents;
        showIntentConfirm.value = true;
      } else {
        // 只有一个意向，直接使用
        localStorage.setItem('current_intent', intents[0].intent_type);
        currentIntent.value = intents[0].intent_type;
        localStorage.setItem('intent_completed', 'true');
        intentConfirmed.value = true;
        // 获取用户列表
        await fetchUsers();
      }
    }
  } catch (error) {
    console.error('检查用户意向失败:', error);
    alert('检查匹配意向失败，请稍后重试');
    router.push('/');
  }
};

const fetchUsers = async () => {
  try {
    const response = await axios.get('http://localhost:5000/api/users');
    if (response.data.status === 'success') {
      users.value = response.data.data.users;
    }
  } catch (error) {
    console.error('获取用户列表失败:', error);
  }
};

const selectIntent = (index) => {
  if (userIntents.value.length > 0 && userIntents.value[index - 1]) {
    localStorage.setItem('current_intent', userIntents.value[index - 1].intent_type);
    currentIntent.value = userIntents.value[index - 1].intent_type;
    localStorage.setItem('intent_completed', 'true');
    showIntentConfirm.value = false;
    intentConfirmed.value = true;
    // 获取用户列表
    fetchUsers();
  }
};

const cancel = () => {
  showIntentConfirm.value = false;
  router.push('/');
};

// 切换意向
const switchIntent = async () => {
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user) return;
  
  try {
    const response = await axios.get('http://localhost:5000/api/intent/' + user.id);
    if (response.data.status === 'success') {
      const intents = response.data.data.intents;
      if (intents.length > 1) {
        // 有多个意向，显示意向确认组件
        userIntents.value = intents;
        showIntentConfirm.value = true;
        intentConfirmed.value = false;
      }
    }
  } catch (error) {
    console.error('获取意向列表失败:', error);
  }
};
/*
const openChatDialog = (user) => {
  // 根据用户创建对应的机器人
  const userBot = {
    id: user.id,
    name: user.name || user.username,
    description: `基于${user.name || user.username}的画像生成的聊天机器人`,
    user_id: user.id
  };
  selectedBot.value = userBot;
  messages.value = [];
  // 添加欢迎消息
  messages.value.push({ content: `你好！我是${user.name || user.username}的聊天机器人，很高兴认识你！` });
};
*/
const closeChatDialog = () => {
  selectedBot.value = null;
  messages.value = [];
  messageInput.value = '';
};
/*
const sendMessage = async () => {
  if (!messageInput.value.trim() || !selectedBot.value) return;
  
  // 添加用户消息
  messages.value.push({ content: messageInput.value, isUser: true });
  const userMessage = messageInput.value;
  messageInput.value = '';
  
  try {
    // 模拟机器人回复
    setTimeout(() => {
      let reply = '';
      if (userMessage.includes('你好') || userMessage.includes('嗨')) {
        reply = `你好！很高兴和你聊天！`;
      } else if (userMessage.includes('名字') || userMessage.includes('叫什么')) {
        reply = `我叫${selectedBot.value.name}，是一个聊天机器人。`;
      } else if (userMessage.includes('兴趣') || userMessage.includes('爱好')) {
        reply = `我的兴趣爱好是${selectedBot.value.description.split('喜欢')[1] || '聊天'}`;
      } else {
        reply = `谢谢你的消息，我很喜欢和你聊天！`;
      }
      messages.value.push({ content: reply });
    }, 1000);
    
    // 保存聊天记录到后端
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
      await axios.post('http://localhost:5000/api/chat', {
        chat_id: `chat_${user.id}_${selectedBot.value.id}`,
        sender: user.id,
        message: userMessage,
        timestamp: new Date().toISOString()
      });
    }
  } catch (error) {
    console.error('发送消息失败:', error);
  }
};
*/

// 获取用户头像
const getUserAvatar = (user) => {
  // 优先使用用户的真实头像
  if (user.avatar) {
    return user.avatar;
  }
  
  // 如果没有头像，使用默认头像
  if (user.gender === '女') {
    return 'http://localhost:5000/avatars/女.jpg';
  } else if(user.gender === '男'){
    return 'http://localhost:5000/avatars/男.jpg';
  }else{
    return 'http://localhost:5000/avatars/null.png';
  }
};
</script>

<style scoped>
.square-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* 意向确认组件样式 */
.intent-confirm-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  min-height: 50vh;
}

.intent-confirm-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  width: 90%;
  max-width: 500px;
  text-align: center;
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.intent-confirm-content h3 {
  margin-bottom: 20px;
  color: #333;
  font-size: 24px;
}

.intent-confirm-content p {
  margin-bottom: 30px;
  color: #666;
  font-size: 16px;
}

.intent-options {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.intent-option {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 15px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 150px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.intent-option:hover {
  background: rgba(255, 255, 255, 0.4);
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.intent-icon {
  font-size: 2rem;
}

.intent-option span {
  font-weight: 600;
  color: #333;
}

.confirm-actions {
  display: flex;
  justify-content: center;
}

.btn-cancel {
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.2);
  color: #333;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .intent-confirm-content {
    padding: 30px;
  }
  
  .intent-confirm-content h3 {
    font-size: 20px;
  }
  
  .intent-confirm-content p {
    font-size: 14px;
  }
  
  .intent-option {
    min-width: 120px;
    padding: 15px;
  }
  
  .intent-icon {
    font-size: 1.5rem;
  }
}

.glass-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
  width: 100%;
  max-width: 1000px;
  min-height: 800px;
}

.square-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.square-header h1 {
  text-align: left;
  margin-bottom: 0;
  color: #333;
  font-size: 28px;
}

.current-intent {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.3);
  padding: 10px 15px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.current-intent span {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.btn-switch-intent {
  padding: 8px 16px;
  background: rgba(37, 99, 235, 0.1);
  color: #2563EB;
  border: 1px solid rgba(37, 99, 235, 0.3);
  border-radius: 15px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-switch-intent:hover {
  background: rgba(37, 99, 235, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(37, 99, 235, 0.2);
}

/* 广场帖子样式 */
.posts-section {
  margin-bottom: 40px;
}

.posts-section h2 {
  margin-bottom: 20px;
  color: #333;
  font-size: 20px;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.post-card {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 15px;
  padding: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.post-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  background: rgba(255, 255, 255, 0.4);
}

.post-header {
  margin-bottom: 15px;
}

.post-author {
  display: flex;
  align-items: center;
  gap: 10px;
}

.author-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(45deg, #6a11cb, #2575fc);
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-name {
  font-weight: 600;
  color: #333;
}

.gender-symbol {
  font-size: 16px;
  font-weight: bold;
}

.post-image {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  border-radius: 8px;
  margin-top: 10px;
  transition: transform 0.3s ease;
}

.post-image:hover {
  transform: scale(1.02);
}

.post-content h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 18px;
}

.post-content p {
  margin: 0 0 15px 0;
  color: #666;
  line-height: 1.5;
}

.post-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.post-action {
  padding: 8px 16px;
  background: rgba(37, 99, 235, 0.1);
  color: #2563EB;
  border: 1px solid rgba(37, 99, 235, 0.3);
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.post-action:hover {
  background: rgba(37, 99, 235, 0.2);
  transform: translateY(-2px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .glass-card {
    padding: 30px;
  }
  
  h1 {
    font-size: 24px;
  }
  
  h2 {
    font-size: 20px;
  }
  
  .square-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .current-intent {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .btn-switch-intent {
    padding: 8px 16px;
    font-size: 14px;
  }
  
  .posts-grid {
    grid-template-columns: 1fr;
  }
  
  .post-card {
    padding: 20px;
  }
  
  .author-avatar {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .author-name {
    font-size: 14px;
  }
  
  .post-content h3 {
    font-size: 16px;
  }
  
  .post-content p {
    font-size: 14px;
  }
  
  .post-stats {
    gap: 15px;
  }
  
  .stat-item {
    font-size: 14px;
  }
  
  .post-action {
    padding: 8px 16px;
    font-size: 14px;
  }
  
  .intent-confirm-content {
    max-width: 90%;
    padding: 30px;
  }
  
  .intent-options {
    flex-direction: column;
  }
  
  .intent-option {
    width: 100%;
  }
  
  .chat-dialog-content {
    max-width: 90%;
    max-height: 80vh;
  }
  
  .chat-messages {
    height: 300px;
  }
  
  .message-input {
    padding: 12px;
  }
  
  .message-input input {
    padding: 12px;
    font-size: 14px;
  }
  
  .message-input button {
    padding: 12px 20px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .glass-card {
    padding: 20px;
  }
  
  h1 {
    font-size: 20px;
  }
  
  h2 {
    font-size: 18px;
  }
  
  .post-card {
    padding: 15px;
  }
  
  .author-avatar {
    width: 35px;
    height: 35px;
    font-size: 14px;
  }
  
  .author-name {
    font-size: 13px;
  }
  
  .post-content h3 {
    font-size: 14px;
  }
  
  .post-content p {
    font-size: 13px;
  }
  
  .post-stats {
    gap: 10px;
  }
  
  .stat-item {
    font-size: 13px;
  }
  
  .post-action {
    padding: 6px 12px;
    font-size: 13px;
  }
  
  .intent-confirm-content {
    max-width: 95%;
    padding: 25px;
  }
  
  .chat-dialog-content {
    max-width: 95%;
    max-height: 75vh;
  }
  
  .chat-messages {
    height: 250px;
  }
  
  .message-input {
    padding: 10px;
  }
  
  .message-input input {
    padding: 10px;
    font-size: 13px;
  }
  
  .message-input button {
    padding: 10px 16px;
    font-size: 13px;
  }
}

/* 聊天对话框样式 */
.chat-dialog {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.chat-dialog-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.chat-dialog-header {
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 20px 20px 0 0;
}

.chat-dialog-header h3 {
  margin: 0;
  color: #333;
  font-size: 20px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  transition: all 0.3s ease;
}

.close-btn:hover {
  color: #333;
  transform: scale(1.1);
}

.chat-dialog-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
  background: rgba(248, 250, 252, 0.5);
}

.message {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  word-wrap: break-word;
}

.bot-message {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.8);
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.user-message {
  align-self: flex-end;
  background: linear-gradient(45deg, #6a11cb, #2575fc);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 4px rgba(106, 17, 203, 0.3);
}

.chat-dialog-input {
  display: flex;
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  gap: 10px;
}

.chat-dialog-input input {
  flex: 1;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  transition: all 0.3s ease;
}

.chat-dialog-input input:focus {
  outline: none;
  border-color: #6a11cb;
  box-shadow: 0 0 0 3px rgba(106, 17, 203, 0.2);
}

.chat-dialog-input button {
  padding: 12px 24px;
  background: linear-gradient(45deg, #6a11cb, #2575fc);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.chat-dialog-input button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(106, 17, 203, 0.4);
}

.chat-dialog-footer {
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0 0 20px 20px;
  display: flex;
  justify-content: center;
}

.friend-request-btn {
  padding: 10px 24px;
  background: rgba(249, 115, 22, 0.1);
  color: #F97316;
  border: 1px solid rgba(249, 115, 22, 0.3);
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.friend-request-btn:hover {
  background: rgba(249, 115, 22, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(249, 115, 22, 0.3);
}

@media (max-width: 768px) {
  .glass-card {
    padding: 20px;
  }
  
  h1 {
    font-size: 24px;
  }
  
  .posts-grid {
    grid-template-columns: 1fr;
  }
  
  .chat-dialog-content {
    width: 95%;
    max-height: 90vh;
  }
  
  .chat-dialog-header,
  .chat-dialog-input,
  .chat-dialog-footer {
    padding: 15px;
  }
  
  .chat-dialog-messages {
    padding: 15px;
  }
}
</style>