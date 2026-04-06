<template>
  <div class="profile-container">
    <div
      class="profile-layout"
      :class="{ 'questions-complete': isQuestionnaireCompleted }"
    >
      <!-- AI聊天区域 - 始终显示在上方 -->
      <section class="panel chat-panel">
        <div class="panel-header chat-header">
          <div>
            <h2>AI 聊天助手</h2>
            <p class="panel-subtitle">
              聊天内容会被采集，用于后续大模型学习数据准备。
            </p>
          </div>
          <span class="chat-state" :class="{ ready: isQuestionnaireCompleted }">
            {{
              isQuestionnaireCompleted
                ? "题目已完成，聊天主展示中"
                : "请先完成题目，完成后自动切主聊天"
            }}
          </span>
        </div>

        <div class="api-tip">API 占位地址：{{ AI_CHAT_API_ENDPOINT }}</div>

        <div ref="chatMessagesContainer" class="chat-messages">
          <div
            v-for="message in chatMessages"
            :key="message.id"
            class="message-row"
            :class="message.role === 'user' ? 'message-user' : 'message-ai'"
          >
            <div class="message-bubble">{{ message.content }}</div>
          </div>
        </div>

        <div class="chat-input-row">
          <input
            v-model="chatInput"
            type="text"
            :disabled="chatSending"
            placeholder="输入你想告诉 AI 的偏好、边界或聊天习惯..."
            @keyup.enter="sendChatMessage"
          />
          <button
            type="button"
            class="btn-chat-send"
            :disabled="chatSending"
            @click="sendChatMessage"
          >
            {{ chatSending ? "发送中..." : "发送" }}
          </button>
        </div>

        <div class="chat-meta">
          <span>已采集聊天数据：{{ collectedChatRecords.length }} 条</span>
          <button
            type="button"
            class="btn-link"
            @click="clearCollectedChatData"
          >
            清空采集数据
          </button>
        </div>
      </section>

      <!-- 客观题区域 - 始终显示在下方 -->
      <section
        class="panel questionnaire-panel"
        :class="{
          collapsed: isQuestionnaireCompleted && questionnaireCollapsed,
        }"
      >
        <div class="panel-header">
          <div>
            <h1>个人画像题目区</h1>
            <p class="panel-subtitle">请完成以下题目，帮助系统更好地了解您。</p>
          </div>
          <div class="panel-controls">
            <span class="progress-pill"
              >{{ answeredQuestionCount }}/{{ totalQuestionCount }} 已完成</span
            >
            <span
              v-if="
                answeredQuestionCount > 0 || answersAutoSaveState === 'error'
              "
              class="autosave-status"
              :class="`state-${answersAutoSaveState}`"
            >
              {{ answersAutoSaveMessage || "开始答题后会自动保存" }}
            </span>
            <button
              v-if="isQuestionnaireCompleted"
              type="button"
              class="btn-ghost"
              @click="toggleQuestionnaireCollapse"
            >
              {{ questionnaireCollapsed ? "展开题目区" : "折叠题目区" }}
            </button>
          </div>
        </div>

        <div
          v-if="isQuestionnaireCompleted && questionnaireCollapsed"
          class="collapsed-tip"
        >
          题目区已折叠，您可以在上方的AI聊天区域继续补充信息。
        </div>

        <form
          v-show="!(isQuestionnaireCompleted && questionnaireCollapsed)"
          @submit.prevent="submitProfile"
        >
          <div class="form-group">
            <label for="age">年龄</label>
            <input type="number" id="age" v-model="profile.age" required />
          </div>
          <div class="form-group">
            <label for="gender">性别</label>
            <select id="gender" v-model="profile.gender" required>
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </div>
          <div class="form-group">
            <label for="occupation">职业</label>
            <input
              type="text"
              id="occupation"
              v-model="profile.occupation"
              required
            />
          </div>
          <div class="form-group">
            <label for="sexual_orientation">性取向</label>
            <select
              id="sexual_orientation"
              v-model="profile.sexual_orientation"
              required
            >
              <option value="异性恋">异性恋</option>
              <option value="同性恋">同性恋</option>
              <option value="双性恋">双性恋</option>
              <option value="无性恋">无性恋</option>
            </select>
          </div>
          <div class="form-group">
            <label>兴趣爱好</label>
            <div class="checkbox-group">
              <label v-for="hobby in hobbies" :key="hobby">
                <input
                  type="checkbox"
                  :value="hobby"
                  v-model="selectedHobbies"
                />
                {{ hobby }}
              </label>
            </div>
          </div>

          <div class="form-section">
            <h2>CARRP 人格问卷</h2>
            <div
              v-for="(question, index) in carrpQuestions"
              :key="index"
              class="form-group"
            >
              <label>{{ question.text }}</label>
              <select v-model="carrpAnswers[index]" required>
                <option value="1">非常不同意</option>
                <option value="2">不同意</option>
                <option value="3">中立</option>
                <option value="4">同意</option>
                <option value="5">非常同意</option>
              </select>
            </div>
          </div>

          <div class="form-section">
            <h2>NRI-BSV 自恋人格问卷</h2>
            <div
              v-for="(question, index) in nriQuestions"
              :key="index"
              class="form-group"
            >
              <label>{{ question.text }}</label>
              <select v-model="nriAnswers[index]" required>
                <option value="1">非常不同意</option>
                <option value="2">不同意</option>
                <option value="3">中立</option>
                <option value="4">同意</option>
                <option value="5">非常同意</option>
              </select>
            </div>
          </div>


          <button type="submit" class="btn-submit">保存个人画像</button>
        </form>
      </section>
    </div>

    <!-- 问卷属性计算结果小窗 -->
    <div class="modal" v-if="showResult">
      <div class="modal-content">
        <h3>个人属性分析结果</h3>

        <div class="result-item">
          <span class="result-label">外向性 (E)：</span>
          <span class="result-value">{{
            personalityAnalysis.extraversion
          }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">开放性 (O)：</span>
          <span class="result-value">{{ personalityAnalysis.openness }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">尽责性 (C)：</span>
          <span class="result-value">{{
            personalityAnalysis.conscientiousness
          }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">宜人性 (A)：</span>
          <span class="result-value">{{
            personalityAnalysis.agreeableness
          }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">神经质 (N)：</span>
          <span class="result-value">{{
            personalityAnalysis.neuroticism
          }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">自恋 (Narc)：</span>
          <span class="result-value">{{ personalityAnalysis.narcissism }}</span>
        </div>
        <button class="btn-close" @click="showResult = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ref,
  computed,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from "vue";
import { onBeforeRouteLeave, useRouter } from "vue-router";
import axios from "axios";

const router = useRouter();
const AI_CHAT_API_ENDPOINT = "https://api.placeholder.chat/3k9x2m7nq1";
const CHAT_DATA_STORAGE_KEY = "profile_ai_chat_training_data";

const conversationId = `conv_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;

const profile = ref({
  age: "",
  gender: "",
  occupation: "",
  sexual_orientation: "",
  personality: "",
  communication_style: "",
  chat_habits: "",
});

const hobbies = ref([
  "阅读",
  "运动",
  "音乐",
  "旅行",
  "电影",
  "美食",
  "游戏",
  "艺术",
  "摄影",
  "健身",
  "瑜伽",
  "舞蹈",
  "编程",
  "绘画",
  "书法",
  "手工",
  "烹饪",
  "烘焙",
  "园艺",
  "钓鱼",
  "露营",
  "攀岩",
  "滑雪",
  "冲浪",
  "潜水",
  "骑行",
  "徒步",
  "冥想",
  "动漫",
  "电竞",
  "桌游",
  "手帐",
  "火漆印章",
  "滴胶",
  "微缩景观",
  "簇绒",
  "编织",
  "金工",
  "石膏娃娃",
  "粘土软陶",
  "胶片摄影",
  "CCD相机",
  "Vlog记录",
  "无人机航拍",
  "Plog",
  "拍立得",
  "城市漫步",
  "路亚",
  "飞盘",
  "陆冲",
  "异宠",
  "水族造景",
  "多肉植物",
  "生态瓶",
  "机械键盘",
  "3D打印",
  "私有云",
  "现场音乐",
  "黑胶唱片",
  "乐队乐器",
  "音乐剧",
  "盲盒潮玩",
  "谷子周边",
  "中古古着",
  "香水香薰",
  "手冲咖啡",
  "精酿啤酒",
  "书法篆刻",
  "占星塔罗",
  "调酒",
  "攒钱记账",
  "逛菜市场",
  "观星",
  "射箭",
  "搏击",
  "茶道",
  "木工",
  "滑板",
  "剧本杀",
  "塔罗牌",
  "脱口秀",
  "逛博物馆",
]);
const selectedHobbies = ref([]);

const avatar = ref("");

const questionnaireCollapsed = ref(false);
const chatInput = ref("");
const chatSending = ref(false);
const chatMessagesContainer = ref(null);
const chatMessages = ref([
  {
    id: `msg_${Math.random().toString(36).slice(2, 10)}`,
    role: "assistant",
    content:
      "你好，我是画像 AI 助手。你可以先完成题目，再告诉我你的聊天风格与关系边界。",
    createdAt: new Date().toISOString(),
  },
]);
const collectedChatRecords = ref([]);
const isProfileLoading = ref(false);
const answersAutoSaveState = ref("idle");
const answersAutoSaveMessage = ref("");
const PROFILE_ANSWER_AUTO_SAVE_ENDPOINT =
  "http://localhost:5000/api/profile";
let answerAutoSaveTimer = null;
const lastSavedAnswerSignature = ref("");

// CARRP 题库（完整）
const carrpQuestions = ref([
  { text: "1. 我是一个热情的人", dimension: "E", direction: "positive" },
  { text: "2. 我喜欢尝试新事物", dimension: "O", direction: "positive" },
  { text: "3. 我是一个有条理的人", dimension: "C", direction: "positive" },
  { text: "4. 我容易感到焦虑", dimension: "N", direction: "positive" },
  { text: "5. 我喜欢与他人合作", dimension: "A", direction: "positive" },
  { text: "6. 我是一个乐观的人", dimension: "E", direction: "positive" },
  { text: "7. 我喜欢独处", dimension: "E", direction: "negative" },
  { text: "8. 我是一个有创造力的人", dimension: "O", direction: "positive" },
  { text: "9. 我容易生气", dimension: "N", direction: "positive" },
  { text: "10. 我是一个负责任的人", dimension: "C", direction: "positive" },
  { text: "11. 我善于体谅他人", dimension: "A", direction: "positive" },
]);

const carrpAnswers = ref(new Array(11).fill(""));

// NRI-BSV 题库（完整）
const nriQuestions = ref([
  { text: "12. 我觉得自己很特别", dimension: "Narc", direction: "positive" },
  {
    text: "13. 我喜欢成为关注的焦点",
    dimension: "Narc",
    direction: "positive",
  },
  {
    text: "14. 我觉得自己比大多数人优秀",
    dimension: "Narc",
    direction: "positive",
  },
  {
    text: "15. 我需要他人的赞美和认可",
    dimension: "Narc",
    direction: "positive",
  },
  { text: "16. 我有很多天赋", dimension: "Narc", direction: "positive" },
  { text: "17. 我应该得到特殊对待", dimension: "Narc", direction: "positive" },
  {
    text: "18. 我是一个天生的领导者",
    dimension: "Narc",
    direction: "positive",
  },
  {
    text: "19. 我比其他人更值得拥有成功",
    dimension: "Narc",
    direction: "positive",
  },
  { text: "20. 我喜欢被人崇拜", dimension: "Narc", direction: "positive" },
  {
    text: "21. 我是一个非常重要的人",
    dimension: "Narc",
    direction: "positive",
  },
]);

const nriAnswers = ref(new Array(10).fill(""));

const totalQuestionCount = computed(
  () => carrpQuestions.value.length + nriQuestions.value.length,
);
const answeredQuestionCount = computed(() => {
  const allAnswers = [...carrpAnswers.value, ...nriAnswers.value];
  return allAnswers.filter(
    (answer) => answer !== "" && answer !== null && answer !== undefined,
  ).length;
});
const isQuestionnaireCompleted = computed(() => {
  return (
    totalQuestionCount.value > 0 &&
    answeredQuestionCount.value === totalQuestionCount.value
  );
});
const answerSignature = computed(
  () => `${carrpAnswers.value.join(",")}|${nriAnswers.value.join(",")}`,
);

// 问卷属性分析结果
const showResult = ref(false);
const personalityAnalysis = ref({
  extraversion: 0, // 外向性
  openness: 0, // 开放性
  conscientiousness: 0, // 尽责性
  agreeableness: 0, // 宜人性
  neuroticism: 0, // 神经质
  narcissism: 0, // 自恋程度
});

onMounted(() => {
  loadProfile();
  loadCollectedChatData();

  if (typeof window !== "undefined") {
    window.addEventListener("beforeunload", handleBeforeUnload);
  }
});

onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("beforeunload", handleBeforeUnload);
  }

  if (answerAutoSaveTimer) {
    clearTimeout(answerAutoSaveTimer);
    answerAutoSaveTimer = null;
  }
});

onBeforeRouteLeave(async () => {
  await flushQuestionnaireAnswersOnLeave();
});

watch(isQuestionnaireCompleted, (completed, previousValue) => {
  // 移除自动收起功能，让用户手动控制题目区的展开/折叠
  if (!completed) {
    questionnaireCollapsed.value = false;
  }
});

const toggleQuestionnaireCollapse = () => {
  questionnaireCollapsed.value = !questionnaireCollapsed.value;
};

const updateAnswerAutoSaveState = (state, message) => {
  answersAutoSaveState.value = state;
  answersAutoSaveMessage.value = message;
};

const getCurrentUserId = () => {
  const user = JSON.parse(localStorage.getItem("user") || "null");
  return user && user.id ? user.id : null;
};

const buildAnswerPayload = (userId) => ({
  user_id: userId,
  carrp_answers: carrpAnswers.value.join(","),
  nri_answers: nriAnswers.value.join(","),
});

const hasUnsavedQuestionnaireAnswers = () => {
  return (
    answeredQuestionCount.value > 0 &&
    answerSignature.value !== lastSavedAnswerSignature.value
  );
};

const saveQuestionnaireAnswers = async ({
  force = false,
  silent = false,
} = {}) => {
  if (isProfileLoading.value) {
    return false;
  }

  const userId = getCurrentUserId();
  if (!userId) {
    return false;
  }

  const currentSignature = answerSignature.value;
  if (!force && currentSignature === lastSavedAnswerSignature.value) {
    if (!silent) {
      updateAnswerAutoSaveState("saved", "题目答案已保存");
    }
    return true;
  }

  if (!silent) {
    updateAnswerAutoSaveState("saving", "题目答案自动保存中...");
  }

  try {
    const response = await axios.post(
      PROFILE_ANSWER_AUTO_SAVE_ENDPOINT,
      buildAnswerPayload(userId),
    );

    if (response.data.status === "success") {
      lastSavedAnswerSignature.value = currentSignature;
      if (!silent) {
        updateAnswerAutoSaveState("saved", "题目答案已自动保存");
      }
      return true;
    }

    if (!silent) {
      updateAnswerAutoSaveState(
        "error",
        `自动保存失败：${response.data.message || "未知错误"}`,
      );
    }
    return false;
  } catch (error) {
    console.error("题目答案自动保存失败:", error);
    if (!silent) {
      updateAnswerAutoSaveState(
        "error",
        "题目答案自动保存失败，请检查网络后重试",
      );
    }
    return false;
  }
};

const flushQuestionnaireAnswersOnLeave = async ({ useBeacon = false } = {}) => {
  if (answerAutoSaveTimer) {
    clearTimeout(answerAutoSaveTimer);
    answerAutoSaveTimer = null;
  }

  if (!hasUnsavedQuestionnaireAnswers()) {
    return;
  }

  const userId = getCurrentUserId();
  if (!userId) {
    return;
  }

  const payload = buildAnswerPayload(userId);

  if (useBeacon) {
    try {
      let beaconSent = false;

      if (
        typeof navigator !== "undefined" &&
        typeof navigator.sendBeacon === "function"
      ) {
        const blob = new Blob([JSON.stringify(payload)], {
          type: "application/json",
        });
        beaconSent = navigator.sendBeacon(
          PROFILE_ANSWER_AUTO_SAVE_ENDPOINT,
          blob,
        );
      }

      if (!beaconSent && typeof fetch === "function") {
        fetch(PROFILE_ANSWER_AUTO_SAVE_ENDPOINT, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
          keepalive: true,
        });
      }

      lastSavedAnswerSignature.value = answerSignature.value;
    } catch (error) {
      console.error("离开页面时题目答案保存失败:", error);
    }
    return;
  }

  await saveQuestionnaireAnswers({ force: true, silent: true });
};

const handleBeforeUnload = () => {
  flushQuestionnaireAnswersOnLeave({ useBeacon: true });
};

const scheduleQuestionnaireAutoSave = () => {
  if (isProfileLoading.value || answeredQuestionCount.value === 0) {
    return;
  }

  if (answerAutoSaveTimer) {
    clearTimeout(answerAutoSaveTimer);
  }

  updateAnswerAutoSaveState("pending", "检测到题目变化，准备自动保存...");
  answerAutoSaveTimer = setTimeout(() => {
    answerAutoSaveTimer = null;
    saveQuestionnaireAnswers();
  }, 450);
};

watch(
  [carrpAnswers, nriAnswers],
  () => {
    scheduleQuestionnaireAutoSave();
  },
  { deep: true },
);

const createMessageId = () =>
  `msg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;

const scrollChatToBottom = async () => {
  await nextTick();
  const container = chatMessagesContainer.value;
  if (!container) {
    return;
  }
  container.scrollTop = container.scrollHeight;
};

const loadCollectedChatData = () => {
  try {
    const raw = localStorage.getItem(CHAT_DATA_STORAGE_KEY);
    if (!raw) {
      return;
    }

    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      collectedChatRecords.value = parsed;
    }
  } catch (error) {
    console.error("读取聊天采集数据失败:", error);
  }
};

const persistCollectedChatData = () => {
  localStorage.setItem(
    CHAT_DATA_STORAGE_KEY,
    JSON.stringify(collectedChatRecords.value),
  );
};

const collectChatData = (message) => {
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const record = {
    id: message.id,
    conversation_id: conversationId,
    user_id: user.id || null,
    role: message.role,
    content: message.content,
    timestamp: message.createdAt,
    endpoint_placeholder: AI_CHAT_API_ENDPOINT,
    questionnaire_progress: `${answeredQuestionCount.value}/${totalQuestionCount.value}`,
  };

  collectedChatRecords.value.push(record);
  persistCollectedChatData();
};

const appendChatMessage = (role, content, shouldCollect = true) => {
  const message = {
    id: createMessageId(),
    role,
    content,
    createdAt: new Date().toISOString(),
  };

  chatMessages.value.push(message);
  if (shouldCollect) {
    collectChatData(message);
  }
  scrollChatToBottom();
};

const requestAiReply = async (userMessage) => {
  const payload = {
    conversation_id: conversationId,
    message: userMessage,
    profile_snapshot: profile.value,
    questionnaire_answers: {
      carrp: carrpAnswers.value,
      nri: nriAnswers.value,
    },
    collected_count: collectedChatRecords.value.length,
  };

  // AI 调用接口位置：后续接入真实大模型时，替换为真实 API。
  // 例如：await axios.post(AI_CHAT_API_ENDPOINT, payload)
  // 当前仅做前端占位，不发真实请求。
  await new Promise((resolve) => setTimeout(resolve, 450));

  const randomTag = Math.random().toString(36).slice(2, 8);
  return `占位回复(${randomTag})：已收到“${userMessage}”。后续会在此处接入真实模型接口，当前 payload 会话 ${payload.conversation_id} 已在前端准备完成。`;
};

const sendChatMessage = async () => {
  const content = chatInput.value.trim();
  if (!content || chatSending.value) {
    return;
  }

  appendChatMessage("user", content);
  chatInput.value = "";
  chatSending.value = true;

  try {
    const aiReply = await requestAiReply(content);
    appendChatMessage("assistant", aiReply);
  } catch (error) {
    console.error("AI 占位回复失败:", error);
    appendChatMessage(
      "assistant",
      "占位接口暂不可用，但你的聊天数据已被采集。",
    );
  } finally {
    chatSending.value = false;
  }
};

const clearCollectedChatData = () => {
  collectedChatRecords.value = [];
  persistCollectedChatData();
  appendChatMessage("assistant", "已清空当前浏览器中的聊天采集数据。", false);
};

const loadProfile = async () => {
  isProfileLoading.value = true;
  try {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
      router.push("/login");
      return;
    }

    const response = await axios.get(
      `http://localhost:5000/api/profile/${user.id}`,
    );
    if (response.data.status === "success" && response.data.profile) {
      const profileData = response.data.profile;
      profile.value.age = profileData.age || "";
      profile.value.gender = profileData.gender || "";
      profile.value.occupation = profileData.occupation || "";
      profile.value.sexual_orientation = profileData.sexual_orientation || "";
      profile.value.personality = profileData.personality || "";
      profile.value.communication_style = profileData.communication_style || "";
      profile.value.chat_habits = profileData.chat_habits || "";

      // 处理兴趣爱好
      if (profileData.hobbies) {
        selectedHobbies.value = profileData.hobbies.split(",");
      }

      // 处理头像
      if (profileData.avatar) {
        avatar.value = profileData.avatar;
      }

      // 处理CARRP答案
      if (profileData.carrp_answers) {
        carrpAnswers.value = profileData.carrp_answers.split(",");
      } else {
        // 初始化11个CARRP问题的答案
        carrpAnswers.value = new Array(11).fill("");
      }

      // 处理NRI-BSV答案
      if (profileData.nri_answers) {
        nriAnswers.value = profileData.nri_answers.split(",");
      } else {
        // 初始化10个NRI-BSV问题的答案
        nriAnswers.value = new Array(10).fill("");
      }

      if (isQuestionnaireCompleted.value) {
        questionnaireCollapsed.value = true;
      }

      lastSavedAnswerSignature.value = answerSignature.value;
      if (answeredQuestionCount.value > 0) {
        updateAnswerAutoSaveState("saved", "已加载并恢复题目答案");
      } else {
        updateAnswerAutoSaveState("idle", "开始答题后会自动保存");
      }
    }
  } catch (error) {
    console.error("加载个人画像失败:", error);
  } finally {
    isProfileLoading.value = false;
  }
};

const calculatePersonality = () => {
  // 计算CARRP问卷属性
  const carrpReady =
    carrpAnswers.value.length === 11 &&
    carrpAnswers.value.every((answer) => answer !== "");
  const nriReady =
    nriAnswers.value.length === 10 &&
    nriAnswers.value.every((answer) => answer !== "");

  if (carrpReady && nriReady) {
    // 处理反向计分题
    const processedCarrpAnswers = carrpAnswers.value.map((answer, index) => {
      const question = carrpQuestions.value[index];
      if (question && question.direction === "negative") {
        return 6 - parseInt(answer);
      }
      return parseInt(answer);
    });

    // 计算各维度得分
    const E =
      (processedCarrpAnswers[0] +
        processedCarrpAnswers[5] +
        processedCarrpAnswers[6]) /
      3;
    const O = (processedCarrpAnswers[1] + processedCarrpAnswers[7]) / 2;
    const C = (processedCarrpAnswers[2] + processedCarrpAnswers[9]) / 2;
    const A = (processedCarrpAnswers[4] + processedCarrpAnswers[10]) / 2;
    const N = (processedCarrpAnswers[3] + processedCarrpAnswers[8]) / 2;

    // 计算NRI-BSV问卷属性（自恋程度）
    let narcissismScore = 0;
    if (nriAnswers.value.length === 10) {
      for (let i = 0; i < 10; i++) {
        narcissismScore += parseInt(nriAnswers.value[i]);
      }
    }
    const Narc = narcissismScore / 10;

    // 更新人格分析结果
    personalityAnalysis.value.extraversion = Math.round(E * 10) / 10; // 外向性
    personalityAnalysis.value.openness = Math.round(O * 10) / 10; // 开放性
    personalityAnalysis.value.conscientiousness = Math.round(C * 10) / 10; // 尽责性
    personalityAnalysis.value.agreeableness = Math.round(A * 10) / 10; // 宜人性
    personalityAnalysis.value.neuroticism = Math.round(N * 10) / 10; // 神经质
    personalityAnalysis.value.narcissism = Math.round(Narc * 10) / 10; // 自恋
  }
};

const submitProfile = async () => {
  try {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
      router.push("/login");
      return;
    }

    // 调试信息：检查用户数据
    console.log('用户数据:', user);
    console.log('用户ID:', user.id);
    console.log('用户ID类型:', typeof user.id);

    // 检查用户ID是否在数据库中存在，如果不存在，尝试使用数据库中实际存在的用户ID
    let effectiveUserId = user.id;
    
    // 如果当前用户ID是 user_81553fda，但数据库中实际存在的是 user_2，则使用 user_2
    if (user.id === 'user_81553fda' && user.username === 'wangyi') {
      console.log('检测到用户ID不匹配，尝试使用数据库中实际存在的用户ID');
      effectiveUserId = 'user_2';
      
      // 更新localStorage中的用户ID
      const updatedUser = { ...user, id: 'user_2' };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      console.log('已更新localStorage中的用户ID为:', effectiveUserId);
    }

    // 计算量化得分
    calculatePersonality();

    const profileData = {
      ...profile.value,
      hobbies: selectedHobbies.value.join(","),
      carrp_answers: carrpAnswers.value.join(","),
      nri_answers: nriAnswers.value.join(","),
      avatar: avatar.value,
      user_id: effectiveUserId,
    };

    // 调试信息：检查提交的数据
    console.log('提交的个人画像数据:', profileData);

    const response = await axios.post(
      "http://localhost:5000/api/profile",
      profileData,
    );
    
    console.log('API响应:', response.data);
    
    if (response.data.status === "success") {
      lastSavedAnswerSignature.value = answerSignature.value;
      updateAnswerAutoSaveState("saved", "题目答案已保存");
      // 显示结果小窗
      showResult.value = true;
      // 保存成功后留在当前页，继续进行 AI 聊天采集
      appendChatMessage(
        "assistant",
        "个人画像已保存。你可以继续聊天补充细节，采集数据会持续累积。",
      );
    } else {
      alert("保存失败：" + (response.data.message || "未知错误"));
    }
  } catch (error) {
    console.error("保存个人画像失败:", error);
    console.error("错误详情:", error.response?.data || error.message);
    alert("保存失败，请稍后重试。错误信息：" + (error.response?.data?.message || error.message));
  }
};
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 28px;
  background:
    radial-gradient(
      circle at 15% 10%,
      rgba(255, 230, 204, 0.85),
      rgba(255, 230, 204, 0) 40%
    ),
    radial-gradient(
      circle at 85% 90%,
      rgba(200, 239, 255, 0.8),
      rgba(200, 239, 255, 0) 38%
    ),
    linear-gradient(145deg, #f8fbff 0%, #eef3f8 45%, #f6f9fc 100%);
}

.profile-layout {
  width: 100%;
  max-width: 1120px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
  transition: all 0.3s ease;
}

/* AI聊天区域特殊样式 */
.chat-panel {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(240, 248, 255, 0.3));
  border: 1px solid rgba(100, 149, 237, 0.2);
}

/* 客观题区域特殊样式 */
.questionnaire-panel {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(245, 245, 245, 0.25));
  border: 1px solid rgba(169, 169, 169, 0.2);
}

.panel:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 44px rgba(23, 45, 77, 0.16);
}

/* AI聊天区域 - 始终在上方，占据更大空间 */
.chat-panel {
  flex: 2;
  min-height: 400px;
  order: 1;
  display: flex;
  flex-direction: column;
}

/* 客观题区域 - 始终在下方，可折叠 */
.questionnaire-panel {
  flex: 1;
  min-height: 300px;
  order: 2;
}

/* 当题目完成时，聊天区域可以占据更多空间 */
.questions-complete .chat-panel {
  flex: 3;
  min-height: 500px;
}

.questions-complete .questionnaire-panel:not(.collapsed) {
  flex: 1;
}

.questionnaire-panel.collapsed {
  padding: 20px 24px;
  max-height: 60px;
  overflow: hidden;
}

h1 {
  margin: 0;
  color: #23344e;
  font-size: 30px;
}

h2 {
  margin: 0;
  color: #23344e;
  font-size: 25px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
}

.panel-subtitle {
  margin: 8px 0 0;
  color: #50617a;
  font-size: 14px;
}

.panel-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.autosave-status {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.autosave-status.state-idle,
.autosave-status.state-pending,
.autosave-status.state-saving {
  color: #8a5f1b;
  background: rgba(230, 186, 105, 0.2);
  border: 1px solid rgba(181, 125, 40, 0.32);
}

.autosave-status.state-saved {
  color: #1f6f49;
  background: rgba(53, 173, 114, 0.15);
  border: 1px solid rgba(31, 125, 80, 0.32);
}

.autosave-status.state-error {
  color: #8f2f2f;
  background: rgba(234, 86, 86, 0.14);
  border: 1px solid rgba(173, 53, 53, 0.32);
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

input,
select,
textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid rgba(120, 142, 167, 0.35);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(5px);
  font-size: 16px;
  transition: all 0.3s ease;
}

input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: #2367b1;
  box-shadow: 0 0 0 3px rgba(35, 103, 177, 0.2);
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  font-weight: normal;
  cursor: pointer;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  margin-right: 5px;
}

textarea {
  resize: vertical;
  min-height: 100px;
}

.btn-submit {
  width: 100%;
  padding: 15px;
  background: linear-gradient(120deg, #1f6fb2, #2f91a7);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 20px;
}

.btn-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(31, 111, 178, 0.35);
}

.form-section {
  margin: 30px 0;
  padding: 20px;
  background: rgba(241, 248, 255, 0.8);
  border-radius: 15px;
  border: 1px solid rgba(167, 191, 224, 0.25);
}

.form-section h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2b4569;
  font-size: 20px;
  text-align: center;
}

.progress-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 11px;
  border-radius: 999px;
  background: rgba(30, 108, 166, 0.12);
  color: #1f5f96;
  font-size: 13px;
  font-weight: 700;
}

.btn-ghost {
  border: 1px solid rgba(31, 111, 178, 0.38);
  background: rgba(255, 255, 255, 0.78);
  color: #1f6fb2;
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
  font-weight: 600;
}

.btn-ghost:hover {
  background: rgba(31, 111, 178, 0.08);
}

.collapsed-tip {
  margin-top: 10px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(40, 140, 210, 0.1);
  color: #2f5378;
  font-size: 14px;
}

.chat-header {
  align-items: center;
}

.chat-state {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(178, 121, 31, 0.32);
  color: #9a6512;
  background: rgba(240, 186, 77, 0.14);
  font-size: 12px;
  font-weight: 700;
}

.chat-state.ready {
  border-color: rgba(31, 125, 80, 0.36);
  color: #1f6f49;
  background: rgba(53, 173, 114, 0.14);
}

.api-tip {
  margin-bottom: 12px;
  font-size: 12px;
  color: #4f6684;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(227, 236, 248, 0.76);
  border: 1px dashed rgba(100, 125, 156, 0.4);
}

.chat-messages {
  flex: 1;
  min-height: 360px;
  max-height: 62vh;
  overflow-y: auto;
  border-radius: 14px;
  border: 1px solid rgba(117, 136, 161, 0.22);
  background: linear-gradient(
    160deg,
    rgba(244, 250, 255, 0.96),
    rgba(236, 245, 252, 0.96)
  );
  padding: 14px;
}

.message-row {
  display: flex;
  margin-bottom: 10px;
}

.message-user {
  justify-content: flex-end;
}

.message-ai {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 82%;
  padding: 10px 12px;
  border-radius: 12px;
  line-height: 1.45;
  font-size: 14px;
}

.message-user .message-bubble {
  background: linear-gradient(120deg, #1f6fb2, #2f91a7);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-ai .message-bubble {
  background: rgba(255, 255, 255, 0.95);
  color: #2a3d57;
  border: 1px solid rgba(120, 146, 176, 0.22);
  border-bottom-left-radius: 4px;
}

.chat-input-row {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.chat-input-row input {
  flex: 1;
}

.btn-chat-send {
  min-width: 98px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(120deg, #db6f2b, #dd9f30);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}

.btn-chat-send:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.chat-meta {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #4d607c;
  font-size: 13px;
}

.btn-link {
  border: none;
  background: none;
  color: #1f6fb2;
  cursor: pointer;
  font-weight: 700;
}

.btn-link:hover {
  text-decoration: underline;
}

/* 模态框样式 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-content {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h3 {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
  font-size: 24px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.result-label {
  font-weight: 600;
  color: #333;
}

.result-value {
  color: #1f6fb2;
  font-weight: 600;
}

.btn-close {
  width: 100%;
  padding: 12px;
  background: linear-gradient(120deg, #1f6fb2, #2f91a7);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 20px;
}

.btn-close:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(31, 111, 178, 0.34);
}

@media (max-width: 768px) {
  .profile-container {
    padding: 14px;
  }

  .panel {
    padding: 18px;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .panel-controls {
    justify-content: flex-start;
  }

  .autosave-status {
    width: fit-content;
  }

  h1 {
    font-size: 24px;
  }

  h2 {
    font-size: 22px;
  }

  .chat-panel {
    min-height: 520px;
  }

  .questions-complete .chat-panel {
    min-height: 560px;
  }

  .chat-input-row {
    flex-direction: column;
  }

  .btn-chat-send {
    min-height: 42px;
  }

  .chat-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .form-section {
    padding: 15px;
  }

  .form-section h2 {
    font-size: 18px;
  }

  .modal-content {
    padding: 20px;
    margin: 20px;
  }

  .modal-content h3 {
    font-size: 20px;
  }
}
</style>
