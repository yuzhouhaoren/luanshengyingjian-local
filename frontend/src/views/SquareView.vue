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
          <div class="post-card" v-for="post in posts" :key="post.id" @click="viewPostDetail(post)">
            <div class="post-header">
              <div class="post-author">
                <div class="author-avatar">{{ post.username ? post.username.charAt(0) : 'U' }}</div>
                <div class="author-info">
                  <span class="author-name">{{ post.username }}</span>
                </div>
              </div>
            </div>
            <div class="post-content">
              <h3>{{ post.title }}</h3>
              <p>{{ typeof post.content === 'string' ? post.content : post.content.content }}</p>
            </div>
            <div class="post-footer">
              <div class="post-tags">
                <span class="tag" v-for="(tag, index) in post.tags" :key="index">{{ tag }}</span>
              </div>
              <button class="post-action" @click.stop="openChatDialog(post)">和Ta聊聊</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 帖子详情页 -->
    <div v-else-if="selectedPost" class="glass-card">
      <div class="post-detail-header">
        <button class="back-btn" @click="backToSquare">&larr; 返回广场</button>
        <h1>{{ selectedPost.title }}</h1>
      </div>
      <div class="post-detail-content">
        <div class="post-detail-author">
          <div class="author-avatar">{{ selectedPost.username ? selectedPost.username.charAt(0) : 'U' }}</div>
          <div class="author-info">
            <span class="author-name">{{ selectedPost.username }}</span>
            <span class="post-time">{{ formatTime(selectedPost.created_at) }}</span>
          </div>
        </div>
        <div class="post-detail-body">
          <p>{{ typeof selectedPost.content === 'string' ? selectedPost.content : selectedPost.content.content }}</p>
          <div class="post-tags">
            <span class="tag" v-for="(tag, index) in selectedPost.tags" :key="index">{{ tag }}</span>
          </div>
        </div>
        <div class="post-detail-actions">
          <button class="action-btn chat-btn" @click="openChatDialog(selectedPost)">
            <span class="btn-icon">💬</span>
            <span>开始聊天</span>
          </button>
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
          <div class="favor-score">
            <span>好感度：{{ favorScore }}</span>
            <div class="favor-bar">
              <div class="favor-fill" :style="{ width: favorScore + '%' }"></div>
            </div>
          </div>
          <button class="friend-request-btn" @click="sendFriendRequest">发送交友申请</button>
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
const posts = ref([]);
const selectedPost = ref(null);
const selectedBot = ref(null);
const messages = ref([]);
const messageInput = ref('');
const showIntentConfirm = ref(false);
const userIntents = ref([]);
const intentConfirmed = ref(false);
const currentIntent = ref('');
const favorScore = ref(0);

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
      if (!profile.age || !profile.gender || !profile.occupation || !profile.sexual_orientation || !profile.personality || !profile.communication_style) {
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
        // 获取帖子列表
        await fetchPosts();
      }
    }
  } catch (error) {
    console.error('检查用户意向失败:', error);
    alert('检查匹配意向失败，请稍后重试');
    router.push('/');
  }
};

const fetchPosts = async () => {
  try {
    const response = await axios.get('http://localhost:5000/api/square/posts');
    if (response.data.status === 'success') {
      posts.value = response.data.data.posts;
    }
  } catch (error) {
    console.error('获取帖子列表失败:', error);
  }
};

const selectIntent = (index) => {
  if (userIntents.value.length > 0 && userIntents.value[index - 1]) {
    localStorage.setItem('current_intent', userIntents.value[index - 1].intent_type);
    currentIntent.value = userIntents.value[index - 1].intent_type;
    localStorage.setItem('intent_completed', 'true');
    showIntentConfirm.value = false;
    intentConfirmed.value = true;
    // 获取帖子列表
    fetchPosts();
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

const viewPostDetail = (post) => {
  selectedPost.value = post;
  intentConfirmed.value = false;
};

const backToSquare = () => {
  selectedPost.value = null;
  intentConfirmed.value = true;
};

const formatTime = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleString();
};

const openChatDialog = (post) => {
  // 创建会话
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user) {
    alert('请先登录');
    router.push('/login');
    return;
  }
  
  // 根据帖子创建对应的机器人
  const userBot = {
    id: post.id,
    name: post.username,
    post_id: post.id,
    user_id: post.user_id
  };
  selectedBot.value = userBot;
  
  // 生成聊天ID
  const chatId = `chat_${user.id}_${post.id}`;
  console.log('打开聊天，post.id:', post.id);
  console.log('打开聊天，selectedBot.id:', selectedBot.value.id);
  console.log('打开聊天，chatId:', chatId);
  
  // 加载聊天历史
  loadChatHistory(chatId);
  
  // 加载好感度
  loadFavorScore(user.id, post.id);
  
  // 获取用户人设提示词
  axios.get(`http://localhost:5000/api/profile/prompt/${post.user_id}`)
    .then(response => {
      if (response.data.status === 'success') {
        const prompt = response.data.prompt;
        // 如果没有历史消息，添加欢迎消息
        if (messages.value.length === 0) {
          messages.value.push({ content: `你好！我是${post.username}，很高兴认识你！` });
        }
      }
    })
    .catch(error => {
      console.error('获取用户人设失败:', error);
      // 如果没有历史消息，添加默认欢迎消息
      if (messages.value.length === 0) {
        messages.value.push({ content: `你好！我是${post.username}，很高兴认识你！` });
      }
    });
};

const loadChatHistory = (chatId) => {
  console.log('加载聊天历史，chatId:', chatId);
  axios.get(`http://localhost:5000/api/chat/history/${chatId}`)
    .then(response => {
      console.log('加载聊天历史响应:', response.data);
      if (response.data.status === 'success') {
        const history = response.data.history || [];
        console.log('聊天历史数据:', history);
        if (history.length > 0) {
          // 确保messages.value被正确赋值
          const mappedMessages = history.map(msg => ({
            content: msg.message || '',
            isUser: msg.sender_type === 'user'
          }));
          console.log('转换后的消息:', mappedMessages);
          messages.value = mappedMessages;
          console.log('messages.value after assignment:', messages.value);
        } else {
          console.log('聊天历史为空');
          messages.value = [];
        }
      } else {
        console.error('加载聊天历史失败:', response.data.message);
        messages.value = [];
      }
    })
    .catch(error => {
      console.error('加载聊天历史失败:', error);
      messages.value = [];
    });
};

const loadFavorScore = (userId, postId) => {
  // 这里可以从localStorage或后端获取好感度
  const storedScore = localStorage.getItem(`favor_score_${userId}_${postId}`);
  if (storedScore) {
    favorScore.value = parseInt(storedScore);
  } else {
    favorScore.value = 0;
  }
};

const closeChatDialog = () => {
  // 保存好感度到localStorage
  const user = JSON.parse(localStorage.getItem('user'));
  if (user && selectedBot.value) {
    localStorage.setItem(`favor_score_${user.id}_${selectedBot.value.id}`, favorScore.value.toString());
  }
  
  selectedBot.value = null;
  messages.value = [];
  messageInput.value = '';
  // 不重置好感度，保持数据持久化
};

const sendMessage = async () => {
  if (!messageInput.value.trim() || !selectedBot.value) return;
  
  // 添加用户消息
  messages.value.push({ content: messageInput.value, isUser: true });
  const userMessage = messageInput.value;
  messageInput.value = '';
  
  try {
    // 调用后端API获取机器人回复
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
      // 获取用户人设提示词
      const promptResponse = await axios.get(`http://localhost:5000/api/profile/prompt/${selectedBot.value.user_id}`);
      let prompt = "你是一个聊天机器人";
      if (promptResponse.data.status === 'success') {
        prompt = promptResponse.data.prompt;
      }
      
      // 构建消息历史
      const messageHistory = messages.value.map(msg => ({
        role: msg.isUser ? "user" : "assistant",
        content: msg.content
      }));
      
      // 调用大模型API
      const response = await axios.post('http://localhost:5000/api/llm/chat', {
        user_id: user.id,
        messages: [
          { "role": "system", "content": prompt },
          ...messageHistory
        ]
      });
      
      if (response.data.status === 'success') {
        const botReply = response.data.response;
        messages.value.push({ content: botReply });
        
        // 更新好感度
        favorScore.value = Math.min(100, favorScore.value + 5);
        
        // 保存好感度到localStorage
        localStorage.setItem(`favor_score_${user.id}_${selectedBot.value.id}`, favorScore.value.toString());
        
        // 生成聊天ID（与loadChatHistory使用相同的生成逻辑）
        const chatId = `chat_${user.id}_${selectedBot.value.id}`;
        console.log('保存聊天记录，chatId:', chatId);
        console.log('保存聊天记录，user.id:', user.id);
        console.log('保存聊天记录，selectedBot.value.id:', selectedBot.value.id);
        
        // 保存聊天记录到后端
        try {
          const userMsgResponse = await axios.post('http://localhost:5000/api/chat', {
            chat_id: chatId,
            sender: user.id,
            message: userMessage,
            timestamp: new Date().toISOString()
          });
          console.log('保存用户消息成功:', userMsgResponse.data);
          
          // 保存机器人回复
          const botMsgResponse = await axios.post('http://localhost:5000/api/chat', {
            chat_id: chatId,
            sender: selectedBot.value.id,
            message: botReply,
            timestamp: new Date().toISOString(),
            sender_type: 'bot'
          });
          console.log('保存机器人消息成功:', botMsgResponse.data);
        } catch (error) {
          console.error('保存聊天记录失败:', error);
        }
      }
    }
  } catch (error) {
    console.error('发送消息失败:', error);
    // 模拟回复
    setTimeout(() => {
      messages.value.push({ content: '抱歉，我暂时无法回复，请稍后再试。' });
    }, 1000);
  }
};

const sendFriendRequest = async () => {
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user || !selectedBot.value) return;
  
  try {
    // 检查好感度是否达到阈值
    if (favorScore.value < 50) {
      alert('好感度不足，需要达到50分才能发送交友申请');
      return;
    }
    
    const response = await axios.post('http://localhost:5000/api/intent-request/send', {
      from_user_id: user.id,
      to_user_id: selectedBot.value.user_id,
      message: '我对你很感兴趣，希望能成为朋友！'
    });
    
    if (response.data.status === 'success') {
      alert('交友申请已发送');
    }
  } catch (error) {
    console.error('发送交友申请失败:', error);
    alert('发送交友申请失败，请稍后重试');
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

/* 帖子详情页样式 */
.post-detail-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  gap: 20px;
}

.back-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.3);
  color: #333;
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

.post-detail-content {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.post-detail-author {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
}

.post-detail-author .author-avatar {
  width: 60px;
  height: 60px;
  font-size: 24px;
}

.post-detail-author .author-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.post-time {
  font-size: 14px;
  color: #666;
}

.post-detail-body {
  margin-bottom: 30px;
  line-height: 1.6;
  color: #333;
}

.post-detail-body p {
  margin-bottom: 20px;
  font-size: 16px;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.tag {
  padding: 6px 12px;
  background: rgba(37, 99, 235, 0.1);
  color: #2563EB;
  border: 1px solid rgba(37, 99, 235, 0.3);
  border-radius: 15px;
  font-size: 14px;
  font-weight: 500;
}

.post-detail-actions {
  display: flex;
  gap: 15px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.chat-btn {
  background: linear-gradient(45deg, #6a11cb, #2575fc);
  color: white;
}

.chat-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(106, 17, 203, 0.4);
}

.btn-icon {
  font-size: 18px;
}

/* 好感度显示样式 */
.favor-score {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.favor-score span {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.favor-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  overflow: hidden;
}

.favor-fill {
  height: 100%;
  background: linear-gradient(90deg, #f97316, #f59e0b);
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* 帖子标签样式 */
.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
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
  
  .post-detail-content {
    padding: 20px;
  }
  
  .post-detail-author .author-avatar {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }
  
  .post-detail-actions {
    flex-direction: column;
  }
  
  .action-btn {
    width: 100%;
    justify-content: center;
  }
  
  .post-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .post-tags {
    margin-top: 10px;
  }
}
</style>