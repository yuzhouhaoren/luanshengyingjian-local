<template>
  <div class="settings-container">
    <div class="glass-card">
      <h1>设置</h1>

      <div class="settings-tabs">
        <button
          :class="{ active: activeTab === 'general' }"
          @click="activeTab = 'general'"
        >
          通用设置
        </button>
        <button
          :class="{ active: activeTab === 'profile' }"
          @click="activeTab = 'profile'"
        >
          个人信息
        </button>
        <button
          :class="{ active: activeTab === 'account' }"
          @click="activeTab = 'account'"
        >
          账号设置
        </button>
      </div>

      <!-- 通用设置 -->
      <form v-if="activeTab === 'general'" @submit.prevent="submitSettings">
        <div class="form-group">
          <label for="notification">通知设置</label>
          <select id="notification" v-model="settings.notification">
            <option value="all">所有通知</option>
            <option value="match">仅匹配通知</option>
            <option value="message">仅消息通知</option>
            <option value="none">关闭所有通知</option>
          </select>
        </div>
        <div class="form-group">
          <label for="privacy">隐私设置</label>
          <select id="privacy" v-model="settings.privacy">
            <option value="public">公开</option>
            <option value="friends">仅朋友可见</option>
            <option value="private">完全私密</option>
          </select>
        </div>
        <div class="form-group">
          <label for="theme">主题设置</label>
          <select id="theme" v-model="settings.theme">
            <option value="light">浅色主题</option>
            <option value="dark">深色主题</option>
            <option value="auto">跟随系统</option>
          </select>
        </div>
        <div class="form-group">
          <label for="language">语言设置</label>
          <select id="language" v-model="settings.language">
            <option value="zh-CN">简体中文</option>
            <option value="en-US">English</option>
          </select>
        </div>
        <button type="submit" class="btn-submit">保存设置</button>
      </form>

      <!-- 个人信息设置 -->
      <form v-if="activeTab === 'profile'" @submit.prevent="submitProfile">
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
          <label for="hobbies">兴趣爱好</label>
          <input
            type="text"
            id="hobbies"
            v-model="hobbiesText"
            placeholder="请用逗号分隔多个爱好"
          />
        </div>
        <div class="form-group">
          <label for="personality">性格特点</label>
          <textarea
            id="personality"
            v-model="profile.personality"
            rows="3"
            placeholder="请描述你的性格特点"
          ></textarea>
        </div>
        <button type="submit" class="btn-submit">保存个人信息</button>
      </form>

      <!-- 账号设置 -->
      <div v-if="activeTab === 'account'" class="account-settings">
        <div class="form-group">
          <label>账号安全</label>
          <div class="account-info">
            <p>当前账号：{{ userEmail }}</p>
          </div>
        </div>
        <div class="form-group">
          <button
            type="button"
            class="btn-danger"
            @click="confirmDeleteAccount"
          >
            注销账号
          </button>
          <p class="danger-note">
            注销账号后，所有数据将被永久删除，不可恢复。
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";

const router = useRouter();
const activeTab = ref("general");

const settings = ref({
  notification: "all",
  privacy: "public",
  theme: "light",
  language: "zh-CN",
});

const profile = ref({
  name: "",
  age: null,
  gender: "",
  occupation: "",
  sexual_orientation: "",
  hobbies: "",
  personality: "",
});

const hobbiesText = computed({
  get: () => profile.value.hobbies,
  set: (value) => {
    profile.value.hobbies = value;
  },
});

const userEmail = ref("");

onMounted(() => {
  loadSettings();
  loadProfile();
  loadUserInfo();
});

const loadUserInfo = () => {
  const savedUser = localStorage.getItem("user");
  if (savedUser) {
    const userObj = JSON.parse(savedUser);
    userEmail.value = userObj.email || "未知";
  }
};

const loadSettings = () => {
  const savedSettings = localStorage.getItem("settings");
  if (savedSettings) {
    settings.value = JSON.parse(savedSettings);
  }
};

const loadProfile = async () => {
  const userId = localStorage.getItem("userId");
  if (!userId) return;

  try {
    const response = await axios.get(
      `http://localhost:5000/api/profile/${userId}`,
    );
    if (response.data.status === "success" && response.data.profile) {
      const data = response.data.profile;
      profile.value = {
        name: data.name || "",
        age: data.age,
        gender: data.gender || "",
        occupation: data.occupation || "",
        sexual_orientation: data.sexual_orientation || "",
        hobbies: data.hobbies || "",
        personality: data.personality || "",
      };
    }
  } catch (error) {
    console.error("加载个人信息失败:", error);
  }
};

const submitSettings = () => {
  localStorage.setItem("settings", JSON.stringify(settings.value));
  alert("设置保存成功！");
};

const submitProfile = async () => {
  const savedUser = localStorage.getItem("user");
  if (!savedUser) {
    alert("请先登录");
    return;
  }

  const userObj = JSON.parse(savedUser);
  const userId = userObj.id;

  try {
    const response = await axios.post("http://localhost:5000/api/profile", {
      user_id: userId,
      age: profile.value.age,
      gender: profile.value.gender,
      occupation: profile.value.occupation,
      sexual_orientation: profile.value.sexual_orientation,
      hobbies: profile.value.hobbies,
      personality: profile.value.personality,
    });

    if (response.data.status === "success") {
      alert("个人信息保存成功！");
    } else {
      alert("保存失败：" + (response.data.message || "未知错误"));
    }
  } catch (error) {
    console.error("保存个人信息失败:", error);
    alert("保存失败，请稍后重试");
  }
};

const confirmDeleteAccount = async () => {
  if (confirm("确定要注销账号吗？此操作不可恢复。")) {
    try {
      const savedUser = localStorage.getItem("user");
      if (savedUser) {
        const userObj = JSON.parse(savedUser);
        // 调用后端API注销账号
        const response = await axios.post(
          "http://localhost:5000/api/account/delete",
          {
            user_id: userObj.id,
          },
        );

        if (response.data.status === "success") {
          localStorage.removeItem("user");
          localStorage.removeItem("intent_completed");
          window.location.href = "/login";
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
.settings-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #1e293b;
  font-size: 28px;
}

.settings-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

.settings-tabs button {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 10px;
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.settings-tabs button.active {
  background: #2563eb;
  color: white;
}

.settings-tabs button:hover:not(.active) {
  background: rgba(37, 99, 235, 0.2);
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #1e293b;
}

input,
select,
textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(5px);
  font-size: 16px;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}

textarea {
  resize: vertical;
  min-height: 80px;
}

.btn-submit {
  width: 100%;
  padding: 15px;
  background: linear-gradient(45deg, #6a11cb, #2575fc);
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
  box-shadow: 0 4px 12px rgba(106, 17, 203, 0.4);
}

/* 账号设置样式 */
.account-info {
  background: rgba(255, 255, 255, 0.3);
  padding: 15px;
  border-radius: 8px;
  margin-top: 10px;
}

.account-info p {
  margin: 5px 0;
  color: #1e293b;
  font-size: 14px;
}

.btn-danger {
  width: 100%;
  padding: 15px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 10px;
}

.btn-danger:hover {
  background: #dc2626;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.danger-note {
  color: #ef4444;
  font-size: 12px;
  margin-top: 10px;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .glass-card {
    padding: 30px;
  }

  h1 {
    font-size: 24px;
  }

  .settings-tabs {
    flex-wrap: wrap;
  }

  .settings-tabs button {
    flex: 1 1 48%;
    padding: 10px;
    font-size: 14px;
  }

  input,
  select,
  textarea {
    padding: 10px;
    font-size: 14px;
  }

  .btn-submit {
    padding: 12px;
    font-size: 14px;
  }

  .btn-danger {
    padding: 12px;
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

  .settings-tabs {
    flex-direction: column;
  }

  .settings-tabs button {
    padding: 8px;
    font-size: 13px;
  }

  input,
  select,
  textarea {
    padding: 8px;
    font-size: 13px;
  }

  .btn-submit {
    padding: 10px;
    font-size: 13px;
  }

  .btn-danger {
    padding: 10px;
    font-size: 13px;
  }

  .settings-tabs button {
    flex: 1 1 100%;
  }
}
</style>
