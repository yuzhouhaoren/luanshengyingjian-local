<template>
  <div class="intent-container">
    <div class="glass-card">
      <h1>匹配意向</h1>
      
      <!-- 意向选择 -->
      <div v-if="!selectedIntent" class="intent-selection">
        <h2>请选择您的匹配意向</h2>
        <p class="intent-hint">您可以选择多个意向类型，分别填写相应的问卷</p>
        <div class="intent-options">
          <div class="intent-option" @click="selectIntent('伴侣')">
            <div class="intent-icon">❤️</div>
            <h3>伴侣</h3>
            <p>寻找浪漫关系，建立长期伴侣关系</p>
          </div>
          <div class="intent-option" @click="selectIntent('志趣相投的朋友')">
            <div class="intent-icon">🤝</div>
            <h3>志趣相投的朋友</h3>
            <p>寻找有共同兴趣爱好的朋友，建立友谊</p>
          </div>
        </div>
        <div class="intent-footer" v-if="completedIntents.length > 0">
          <h3>已完成的意向：</h3>
          <div class="completed-intent-list">
            <span class="completed-intent" v-for="intent in completedIntents" :key="intent">
              {{ intent }}
            </span>
          </div>
          <button class="btn-continue" @click="goToSquare">前往聊天广场</button>
        </div>
      </div>
      
      <!-- 答题界面 -->
      <div v-else class="intent-questions">
        <h2>{{ selectedIntent }}匹配意向答题</h2>
        <form @submit.prevent="submitAnswers">
          <div v-for="(question, index) in questions" :key="index" class="form-group">
            <label>{{ question.text }}</label>
            
            <!-- 单选题 -->
            <div v-if="question.type === 'single'" class="radio-group">
              <label v-for="option in question.options" :key="option.value" class="radio-option">
                <input type="radio" :name="`question_${index}`" :value="option.value" v-model="answers[index]" required>
                {{ option.label }}
              </label>
            </div>
            
            <!-- 多选题 -->
            <div v-else-if="question.type === 'multiple'" class="checkbox-group">
              <label v-for="option in question.options" :key="option.value" class="checkbox-option">
                <input type="checkbox" :value="option.value" v-model="answers[index]">
                {{ option.label }}
              </label>
              <p class="hint" v-if="question.text.includes('I1') || question.text.includes('V1') || question.text.includes('L2') || question.text.includes('E1') || question.text.includes('G1')">请选择最多5项</p>
              <p class="hint" v-else-if="question.text.includes('P1')">请选择最多3项</p>
            </div>
          </div>
          <div class="form-actions">
            <button type="submit" class="btn-submit">提交答案</button>
            <button type="button" class="btn-back" @click="selectedIntent = null">返回选择</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const selectedIntent = ref(null);
const questions = ref([]);
const answers = ref([]);
const completedIntents = ref([]);

onMounted(() => {
  // 加载用户已完成的意向
  loadCompletedIntents();
});

const loadCompletedIntents = async () => {
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user) return;
  
  try {
    const response = await axios.get('http://localhost:5000/api/intent/' + user.id);
    if (response.data.status === 'success') {
      const intents = response.data.data.intents;
      completedIntents.value = intents.map(intent => intent.intent_type);
    }
  } catch (error) {
    console.error('加载已完成意向失败:', error);
  }
};

const selectIntent = (intent) => {
  selectedIntent.value = intent;
  loadQuestions();
  // 延迟加载已保存的答案，确保问题已加载完成
  setTimeout(() => {
    loadSavedAnswers();
  }, 100);
};

const loadQuestions = () => {
  // 根据选择的意向加载不同的问题
  if (selectedIntent.value === '伴侣') {
    questions.value = [
      // 1. 安全联结维度（S）
      {
        text: 'S1. 对方超过多少小时未回复你的重要消息，你会开始感到不安？',
        dimension: 'S',
        type: 'single',
        options: [
          { value: '5', label: '0小时' },
          { value: '4', label: '8小时' },
          { value: '3', label: '16小时' },
          { value: '2', label: '24小时' },
          { value: '1', label: '48小时及以上' }
        ]
      },
      {
        text: 'S2. 你最想锁定哪种「安全感」？（请注意：这同时意味着你要接纳关系中的某种局限性）',
        dimension: 'S',
        type: 'single',
        options: [
          { value: '5', label: '事事有回应 —— 情绪上被时刻呵护，但对方可能缺乏事业野心，难以应对现实风浪' },
          { value: '4', label: '绝对的后盾 —— 现实中有靠山，但对方可能不细腻呵护，日常相处显得乏味、无趣' },
          { value: '3', label: '自由的牵挂 —— 相处轻松没压力，但当你需要高度陪伴时，对方可能显得冷淡疏离' },
          { value: '2', label: '进步的战友 —— 能带你共同成长，但关系更现实，一旦步调不一致或失去价值，容易走散' },
          { value: '1', label: '独立自主 —— 各自独立，互不依赖，但可能缺乏深度联结' }
        ]
      },
      {
        text: 'S3. 以下哪种行为最让你感到信任被破坏？',
        dimension: 'S',
        type: 'single',
        options: [
          { value: '5', label: '与前任保持密切联系' },
          { value: '4', label: '在社交软件上暧昧聊天' },
          { value: '3', label: '重大决定隐瞒不商量' },
          { value: '2', label: '在朋友面前贬低你' },
          { value: '1', label: '经济问题隐瞒' }
        ]
      },
      {
        text: 'S4. 你发现伴侣手机里有和异性的暧昧聊天记录，对方解释只是「普通朋友开玩笑」，你会？',
        dimension: 'S',
        type: 'single',
        options: [
          { value: '5', label: '直接提出分手，认为信任已破裂' },
          { value: '4', label: '要求立即断绝联系，并查看所有聊天记录' },
          { value: '3', label: '冷静沟通，明确表达底线，要求对方做出改变' },
          { value: '2', label: '暂时相信，但会暗中观察一段时间' },
          { value: '1', label: '选择相信，不再提及此事' }
        ]
      },
      {
        text: 'S5. 如果伴侣曾有过一次让你信任受损的行为（如隐瞒重要事情），但事后真诚道歉并努力改正，你会？',
        dimension: 'S',
        type: 'single',
        options: [
          { value: '5', label: '无法继续，信任一旦破裂就无法修复' },
          { value: '4', label: '很难再完全信任，关系受影响' },
          { value: '3', label: '需要时间观察，慢慢重建信任' },
          { value: '2', label: '基本信任，但偶尔会想起' },
          { value: '1', label: '完全信任如初，毫无芥蒂' }
        ]
      },
      // 2. 互动模式维度（I）
      {
        text: 'I1. 发生争执时，你最像以下哪种动物？',
        dimension: 'I',
        type: 'single',
        options: [
          { value: '5', label: '刺猬 —— 保护自我边界，第一时间回应。可能会因为激烈带动，所以应对激烈' },
          { value: '4', label: '海豚 —— 即时主动沟通，试图用理性或幽默化解当前问题' },
          { value: '3', label: '章鱼 —— 将当前问题与过往类似情境联系，倾向于探讨整体模式而非单一事件' },
          { value: '2', label: '树懒 —— 需要较长时间处理情绪，回应较慢，但通常经过深思熟虑' },
          { value: '1', label: '鸵鸟 —— 为回避剧烈冲突需要独处或冷静，之后再沟通或顺其自然' }
        ]
      },
      {
        text: 'I2. 你父母要求你伴侣毕业后回老家考公，伴侣不满地向你抱怨，你会？',
        dimension: 'I',
        type: 'single',
        options: [
          { value: '5', label: '组队 —— 先跟伴侣商量好对策，统一立场后一起跟父母谈' },
          { value: '4', label: '调解 —— 两头做工作，帮双方互相理解' },
          { value: '3', label: '划界限 —— 直接告诉父母「请不要干涉我们的决定」' },
          { value: '2', label: '劝和 —— 帮伴侣分析父母的出发点，劝 TA 试着配合' },
          { value: '1', label: '冷处理 —— 先不表态，等大家冷静下来再说' }
        ]
      },
      {
        text: 'I3. 对于非性接触的亲昵（如出门前的拥抱、沙发上的依偎、牵手散步），你的需求度是？',
        dimension: 'I',
        type: 'single',
        options: [
          { value: '5', label: '必须有大量肢体接触「充电」' },
          { value: '4', label: '经常需要' },
          { value: '3', label: '偶尔需要' },
          { value: '2', label: '不太需要' },
          { value: '1', label: '完全不需要，可以各玩各的' }
        ]
      },
      {
        text: 'I4. 对于性亲密行为（性生活），你的需求度是？',
        dimension: 'I',
        type: 'single',
        options: [
          { value: '5', label: '这是关系的核心粘合剂，非常重要' },
          { value: '4', label: '比较重要，但可以协调' },
          { value: '3', label: '重要但非必需' },
          { value: '2', label: '不太重要，可有可无' },
          { value: '1', label: '无性婚姻也可接受' }
        ]
      },
      {
        text: 'I5. 如果亲密度低于你的期待，你更倾向于？',
        dimension: 'I',
        type: 'single',
        options: [
          { value: '5', label: '主动沟通，坦诚表达自己的需求和感受' },
          { value: '4', label: '创造氛围，通过增加相处情趣来自然提升' },
          { value: '3', label: '观察反思，先检查关系其他方面是否出了问题' },
          { value: '2', label: '难以启齿，但可能会在其他方面表现出不满' },
          { value: '1', label: '顺其自然，相信感情到了自然会亲密' }
        ]
      },
      {
        text: 'I6. 伴侣在朋友面前当众否定你的观点，让你很没面子，你会？',
        dimension: 'I',
        type: 'single',
        options: [
          { value: '5', label: '当场反驳，维护自己的立场' },
          { value: '4', label: '事后私下沟通，表达自己的感受' },
          { value: '3', label: '暂时忍耐，之后减少在公开场合的互动' },
          { value: '2', label: '默默忍受，避免冲突' },
          { value: '1', label: '直接离场，结束这场聚会' }
        ]
      },
      // 3. 现实坐标维度（R）
      {
        text: 'R1. 你对伴侣的收入要求是？',
        dimension: 'R',
        type: 'single',
        options: [
          { value: '5', label: '远高于我' },
          { value: '4', label: '与我相当' },
          { value: '3', label: '略低于我' },
          { value: '2', label: '远低于我' },
          { value: '1', label: '无要求' }
        ]
      },
      {
        text: 'R2. 你对伴侣的家庭背景要求是？',
        dimension: 'R',
        type: 'single',
        options: [
          { value: '5', label: '门当户对' },
          { value: '4', label: '家庭背景相似即可' },
          { value: '3', label: '家庭氛围和谐即可' },
          { value: '2', label: '不太在意，但希望简单' },
          { value: '1', label: '无要求' }
        ]
      },
      {
        text: 'R3. 伴侣突然提出要裸辞创业，启动资金需要你拿出一半积蓄，且没有明确的盈利计划。你会？',
        dimension: 'R',
        type: 'single',
        options: [
          { value: '5', label: '直接分手，认为对方不负责任' },
          { value: '4', label: '坚决反对，要求对方先有完整方案再谈' },
          { value: '3', label: '支持，但要求签订书面协议，明确权责' },
          { value: '2', label: '犹豫，但最终会支持，相信对方的能力' },
          { value: '1', label: '无条件支持，愿意共同承担风险' }
        ]
      },
      {
        text: 'R4. 伴侣的父母要求你们婚后必须同住，你会？',
        dimension: 'R',
        type: 'single',
        options: [
          { value: '5', label: '明确拒绝，坚持婚后独立居住' },
          { value: '4', label: '可以短期同住，但有明确的搬离计划' },
          { value: '3', label: '同意同住，但要求划分清晰的生活边界' },
          { value: '2', label: '顺从伴侣的决定，自己适应' },
          { value: '1', label: '主动提出同住，以维系家庭关系' }
        ]
      },
      {
        text: 'R5. 伴侣所在公司突然裁员，TA 失业在家，情绪低落，你会？',
        dimension: 'R',
        type: 'single',
        options: [
          { value: '5', label: '提出分手，担心未来生活质量受影响' },
          { value: '4', label: '感到压力，开始重新评估关系稳定性' },
          { value: '3', label: '保持中立，让 TA 自己消化情绪' },
          { value: '2', label: '提供经济支持，鼓励 TA 调整心态' },
          { value: '1', label: '帮 TA 分析职业规划，一起找新机会' }
        ]
      },
      // 4. 意义系统维度（M）
      {
        text: 'M1. 你对人生目标和精神追求的重视程度如何？',
        dimension: 'M',
        type: 'single',
        options: [
          { value: '5', label: '非常重视，它们是我生活的核心' },
          { value: '4', label: '比较重视，会花时间思考和实践' },
          { value: '3', label: '一般，有目标但不会强求' },
          { value: '2', label: '不太重视，更关注当下生活' },
          { value: '1', label: '完全不重视，随遇而安' }
        ]
      },
      {
        text: 'M2. 你对伴侣的价值观契合度要求是？',
        dimension: 'M',
        type: 'single',
        options: [
          { value: '5', label: '高度一致' },
          { value: '4', label: '核心一致，细节可包容' },
          { value: '3', label: '求同存异即可' },
          { value: '2', label: '大致相同即可' },
          { value: '1', label: '无要求' }
        ]
      },
      {
        text: 'M3. 伴侣为了追求个人理想，决定放弃稳定工作去偏远地区支教 5 年，你会？',
        dimension: 'M',
        type: 'single',
        options: [
          { value: '5', label: '全力支持，愿意异地并规划未来团聚' },
          { value: '4', label: '支持，但要求对方定期沟通，共同调整计划' },
          { value: '3', label: '犹豫，担心关系受到影响，需要时间考虑' },
          { value: '2', label: '反对，认为理想不能凌驾于现实之上' },
          { value: '1', label: '提出分手，无法接受长期分离' }
        ]
      },
      {
        text: 'M4. 伴侣的核心价值观与你严重冲突（例如你重视环保，对方却认为环保是小题大做），你会？',
        dimension: 'M',
        type: 'single',
        options: [
          { value: '5', label: '深度沟通，尝试引导对方理解你的立场' },
          { value: '4', label: '求同存异，尊重对方观点但坚持自己的原则' },
          { value: '3', label: '减少相关话题的讨论，避免冲突' },
          { value: '2', label: '逐渐疏远，认为价值观不合难以长久' },
          { value: '1', label: '直接分手，价值观是关系的基石' }
        ]
      },
      {
        text: 'M5. 你和伴侣对「成功人生」的定义完全不同，你会？',
        dimension: 'M',
        type: 'single',
        options: [
          { value: '5', label: '深度探讨，尝试找到双方都认可的新定义' },
          { value: '4', label: '尊重彼此的定义，各自追求自己的目标' },
          { value: '3', label: '减少对未来的规划，专注当下的生活' },
          { value: '2', label: '感到迷茫，重新思考这段关系的意义' },
          { value: '1', label: '提出分手，认为人生方向不同无法同行' }
        ]
      },
      // 5. 动力发展维度（D）
      {
        text: 'D1. 你希望关系的发展节奏是？',
        dimension: 'D',
        type: 'single',
        options: [
          { value: '5', label: '快速推进，明确未来' },
          { value: '4', label: '稳步发展，有共同规划' },
          { value: '3', label: '顺其自然，但希望有未来' },
          { value: '2', label: '慢慢来，不着急' },
          { value: '1', label: '保持现状，不考虑未来' }
        ]
      },
      {
        text: 'D2. 你对伴侣的成长速度要求是？',
        dimension: 'D',
        type: 'single',
        options: [
          { value: '5', label: '与我同步' },
          { value: '4', label: '略快于我，带动我' },
          { value: '3', label: '与我相当' },
          { value: '2', label: '略慢于我，我带动' },
          { value: '1', label: '无要求' }
        ]
      },
      {
        text: 'D3. 你在事业上快速晋升，而伴侣却陷入职业瓶颈，长期停滞不前，你会？',
        dimension: 'D',
        type: 'single',
        options: [
          { value: '5', label: '主动提供帮助，制定计划共同成长' },
          { value: '4', label: '鼓励对方，耐心陪伴其走出困境' },
          { value: '3', label: '保持距离，专注于自己的发展' },
          { value: '2', label: '感到失望，重新评估关系的未来' },
          { value: '1', label: '提出分手，认为双方已不在同一轨道' }
        ]
      },
      {
        text: 'D4. 关系进入稳定期后，你发现双方都失去了激情，发展停滞。你会？',
        dimension: 'D',
        type: 'single',
        options: [
          { value: '5', label: '主动发起改变，尝试新的相处模式' },
          { value: '4', label: '与伴侣沟通，共同寻找新的动力' },
          { value: '3', label: '耐心等待，相信时间会带来转机' },
          { value: '2', label: '感到疲惫，开始考虑其他可能性' },
          { value: '1', label: '接受现状，认为平淡是关系的常态' }
        ]
      },
      {
        text: 'D5. 伴侣突然提出要去国外深造 2 年，你会？',
        dimension: 'D',
        type: 'single',
        options: [
          { value: '5', label: '全力支持，一起规划异地后的相处模式' },
          { value: '4', label: '支持，但要求明确未来的发展方向' },
          { value: '3', label: '犹豫，担心关系会因距离变淡' },
          { value: '2', label: '反对，认为这会严重影响关系' },
          { value: '1', label: '提出分手，无法接受长期分离' }
        ]
      },
      // 6. 日常系统维度（E）
      {
        text: 'E1. 你对伴侣的生活习惯（如作息、饮食、卫生）要求是？',
        dimension: 'E',
        type: 'single',
        options: [
          { value: '5', label: '高度一致' },
          { value: '4', label: '核心一致，细节可包容' },
          { value: '3', label: '大致相同，可接受差异' },
          { value: '2', label: '不太在意，但希望基本和谐' },
          { value: '1', label: '无要求' }
        ]
      },
      {
        text: 'E2. 你对伴侣的消费观要求是？',
        dimension: 'E',
        type: 'single',
        options: [
          { value: '5', label: '高度一致' },
          { value: '4', label: '核心一致，细节可包容' },
          { value: '3', label: '大致相同，可接受差异' },
          { value: '2', label: '不太在意，但希望基本和谐' },
          { value: '1', label: '无要求' }
        ]
      },
      {
        text: 'E3. 伴侣沉迷游戏，经常熬夜，严重影响你的休息和生活节奏，你会？',
        dimension: 'E',
        type: 'single',
        options: [
          { value: '5', label: '明确提出底线，要求对方立即调整' },
          { value: '4', label: '协商制定规则，共同遵守' },
          { value: '3', label: '尝试适应，调整自己的作息' },
          { value: '2', label: '感到不满，但选择忍耐' },
          { value: '1', label: '搬出去住，减少相处时间' }
        ]
      },
      {
        text: 'E4. 伴侣在消费上大手大脚，经常透支信用卡，而你是储蓄型人格，你会？',
        dimension: 'E',
        type: 'single',
        options: [
          { value: '5', label: '强制共同制定预算，严格控制支出' },
          { value: '4', label: '建立共同账户，明确消费边界' },
          { value: '3', label: '各自管理财务，互不干涉' },
          { value: '2', label: '感到焦虑，但选择包容' },
          { value: '1', label: '提出分手，认为消费观不合无法长久' }
        ]
      },
      {
        text: 'E5. 周末你想宅家休息，伴侣却坚持要外出社交，你会？',
        dimension: 'E',
        type: 'single',
        options: [
          { value: '5', label: '协商折中，比如上午宅家下午外出' },
          { value: '4', label: '尊重对方的选择，一起外出' },
          { value: '3', label: '各自安排，互不干涉' },
          { value: '2', label: '坚持自己的想法，拒绝外出' },
          { value: '1', label: '因此产生矛盾，影响当天的心情' }
        ]
      },
      // 7. 灵魂共振维度（N）
      {
        text: 'N1. 你对伴侣的审美趣味（如音乐、电影、书籍）要求是？',
        dimension: 'N',
        type: 'single',
        options: [
          { value: '5', label: '高度一致' },
          { value: '4', label: '互相欣赏即可' },
          { value: '3', label: '大致相同，可接受差异' },
          { value: '2', label: '不太在意，但希望有共同话题' },
          { value: '1', label: '无要求' }
        ]
      },
      {
        text: 'N2. 你对伴侣的深度理解能力要求是？',
        dimension: 'N',
        type: 'single',
        options: [
          { value: '5', label: '能完全懂我' },
          { value: '4', label: '能懂我大部分' },
          { value: '3', label: '能懂我核心即可' },
          { value: '2', label: '能偶尔懂我' },
          { value: '1', label: '无要求' }
        ]
      },
      {
        text: 'N3. 你分享了一个对自己意义重大的艺术作品（如电影、书籍），伴侣却表示完全无法理解，甚至觉得无聊，你会？',
        dimension: 'N',
        type: 'single',
        options: [
          { value: '5', label: '耐心解释，尝试引导对方感受其魅力' },
          { value: '4', label: '尊重对方的感受，寻找其他共鸣点' },
          { value: '3', label: '感到失落，减少分享这类内容' },
          { value: '2', label: '认为双方精神世界差距太大，重新评估关系' },
          { value: '1', label: '直接分手，认为灵魂无法共振' }
        ]
      },
      {
        text: 'N4. 在你情绪低落、需要深度倾诉时，伴侣总是用理性分析代替情感回应，你会？',
        dimension: 'N',
        type: 'single',
        options: [
          { value: '5', label: '明确表达自己的情感需求，希望对方改变' },
          { value: '4', label: '接受对方的方式，同时寻找其他情感出口' },
          { value: '3', label: '感到孤独，减少深度倾诉' },
          { value: '2', label: '认为对方无法提供精神支持，重新考虑关系' },
          { value: '1', label: '提出分手，认为缺乏深度理解' }
        ]
      },
      {
        text: 'N5. 你和伴侣对同一部深刻的文艺作品有完全相反的解读，你会？',
        dimension: 'N',
        type: 'single',
        options: [
          { value: '5', label: '深入探讨，尝试理解对方的视角' },
          { value: '4', label: '尊重差异，不强迫对方认同自己' },
          { value: '3', label: '减少相关话题的讨论，避免分歧' },
          { value: '2', label: '感到失望，认为对方无法与自己共情' },
          { value: '1', label: '重新评估双方的精神契合度' }
        ]
      }
    ];
  } else if (selectedIntent.value === '志趣相投的朋友') {
    questions.value = [
      // 维度一：兴趣共鸣 (I)
      {
        text: 'I1. 你希望和朋友一起进行哪些活动？（可多选，最多选5项）',
        dimension: 'I',
        type: 'multiple',
        options: [
          { value: '运动健身', label: '运动健身（跑步、球类、健身等）' },
          { value: '阅读写作', label: '阅读写作' },
          { value: '影视动漫', label: '影视动漫（追剧、看电影、动漫）' },
          { value: '游戏电竞', label: '游戏电竞（网游、主机游戏等）' },
          { value: '音乐艺术', label: '音乐艺术（听音乐、看展、演奏）' },
          { value: '户外旅行', label: '户外旅行（登山、露营、旅游）' },
          { value: '美食探店', label: '美食探店' },
          { value: '手工DIY', label: '手工DIY' }
        ]
      },
      {
        text: 'I2. 如果朋友对你热衷的某个爱好完全不感兴趣，你会？',
        dimension: 'I',
        type: 'single',
        options: [
          { value: '5', label: '感到失望，希望找到更有共同话题的朋友' },
          { value: '4', label: '可以接受，但会减少一起做这件事的频率' },
          { value: '3', label: '无所谓，可以各自保留爱好' },
          { value: '2', label: '反而觉得可以拓展自己的视野' },
          { value: '1', label: '完全不在意' }
        ]
      },
      {
        text: 'I3. 你更倾向于拥有？',
        dimension: 'I',
        type: 'single',
        options: [
          { value: '5', label: '一个深度兴趣完全一致的朋友' },
          { value: '4', label: '几个兴趣点重叠的朋友' },
          { value: '3', label: '各种不同兴趣的朋友，可以带我体验新事物' },
          { value: '2', label: '无所谓，聊得来就行' },
          { value: '1', label: '朋友不需要有共同兴趣' }
        ]
      },
      {
        text: 'I4. 对于新接触的爱好，你希望朋友？',
        dimension: 'I',
        type: 'single',
        options: [
          { value: '5', label: '能和我一起从零开始学习' },
          { value: '4', label: '已经是高手可以带我' },
          { value: '3', label: '能偶尔交流心得' },
          { value: '2', label: '不干涉我即可' },
          { value: '1', label: '没想过' }
        ]
      },
      // 维度二：价值观契合 (V)
      {
        text: 'V1. 你认为以下哪些价值观对你来说很重要？（可多选，最多选5项）',
        dimension: 'V',
        type: 'multiple',
        options: [
          { value: '家庭至上', label: '家庭至上' },
          { value: '个人自由', label: '个人自由' },
          { value: '社会责任感', label: '社会责任感' },
          { value: '追求真理', label: '追求真理' },
          { value: '物质财富', label: '物质财富' },
          { value: '精神满足', label: '精神满足' },
          { value: '公平正义', label: '公平正义' },
          { value: '创新冒险', label: '创新冒险' }
        ]
      },
      {
        text: 'V2. 当你和朋友讨论社会热点时，如果观点严重分歧，你会？',
        dimension: 'V',
        type: 'single',
        options: [
          { value: '5', label: '试图说服对方，希望达成一致' },
          { value: '4', label: '深入探讨，了解彼此立场' },
          { value: '3', label: '求同存异，转移话题' },
          { value: '2', label: '感到不适，减少此类讨论' },
          { value: '1', label: '无所谓，不影响友谊' }
        ]
      },
      {
        text: 'V3. 你对朋友的人生观要求是？',
        dimension: 'V',
        type: 'single',
        options: [
          { value: '5', label: '必须高度一致' },
          { value: '4', label: '核心一致即可' },
          { value: '3', label: '可以不同，但能互相理解' },
          { value: '2', label: '不太在意' },
          { value: '1', label: '完全不在意' }
        ]
      },
      {
        text: 'V4. 如果朋友为了追求理想而放弃稳定生活，你会？',
        dimension: 'V',
        type: 'single',
        options: [
          { value: '5', label: '全力支持，并愿意提供帮助' },
          { value: '4', label: '支持但会提醒风险' },
          { value: '3', label: '尊重选择，但不参与' },
          { value: '2', label: '不太理解，但保持距离' },
          { value: '1', label: '反对，认为不切实际' }
        ]
      },
      // 维度三：性格相容 (P)
      {
        text: 'P1. 你更喜欢哪种性格的朋友？（可多选，最多选3项）',
        dimension: 'P',
        type: 'multiple',
        options: [
          { value: '开朗活泼', label: '开朗活泼，能带动气氛' },
          { value: '沉稳内敛', label: '沉稳内敛，善于倾听' },
          { value: '幽默风趣', label: '幽默风趣，常开玩笑' },
          { value: '理性冷静', label: '理性冷静，分析问题' },
          { value: '感性细腻', label: '感性细腻，情感丰富' },
          { value: '独立自主', label: '独立自主，有主见' },
          { value: '随和包容', label: '随和包容，好相处' }
        ]
      },
      {
        text: 'P2. 在社交场合中，你希望朋友？',
        dimension: 'P',
        type: 'single',
        options: [
          { value: '5', label: '和我形影不离' },
          { value: '4', label: '能一起融入圈子' },
          { value: '3', label: '各自活动，偶尔交流' },
          { value: '2', label: '不需要一起出现' },
          { value: '1', label: '无所谓' }
        ]
      },
      {
        text: 'P3. 当遇到困难时，你更倾向于？',
        dimension: 'P',
        type: 'single',
        options: [
          { value: '5', label: '第一时间找朋友倾诉' },
          { value: '4', label: '先自己消化，必要时再找朋友' },
          { value: '3', label: '看情况，不一定找朋友' },
          { value: '2', label: '很少向朋友倾诉' },
          { value: '1', label: '完全自己解决' }
        ]
      },
      {
        text: 'P4. 你对朋友的沟通频率要求是？',
        dimension: 'P',
        type: 'single',
        options: [
          { value: '5', label: '每天都要联系' },
          { value: '4', label: '每周几次' },
          { value: '3', label: '每周一次左右' },
          { value: '2', label: '每月几次' },
          { value: '1', label: '随缘，几个月一次也行' }
        ]
      },
      // 维度四：生活节奏 (L)
      {
        text: 'L1. 你对朋友的作息习惯要求是？',
        dimension: 'L',
        type: 'single',
        options: [
          { value: '5', label: '必须和我一致' },
          { value: '4', label: '大致相同即可' },
          { value: '3', label: '可以不同，但不要互相干扰' },
          { value: '2', label: '无所谓' },
          { value: '1', label: '完全不在意' }
        ]
      },
      {
        text: 'L2. 你希望和朋友一起进行哪些日常活动？（可多选，最多选5项）',
        dimension: 'L',
        type: 'multiple',
        options: [
          { value: '一起吃饭', label: '一起吃饭' },
          { value: '一起逛街', label: '一起逛街' },
          { value: '一起运动', label: '一起运动' },
          { value: '一起看电影', label: '一起看电影' },
          { value: '一起学习', label: '一起学习' },
          { value: '一起旅行', label: '一起旅行' },
          { value: '一起打游戏', label: '一起打游戏' }
        ]
      },
      {
        text: 'L3. 你对朋友的消费观要求是？',
        dimension: 'L',
        type: 'single',
        options: [
          { value: '5', label: '必须一致' },
          { value: '4', label: '核心一致' },
          { value: '3', label: '可以不同，但能互相理解' },
          { value: '2', label: '不太在意' },
          { value: '1', label: '完全不在意' }
        ]
      },
      {
        text: 'L4. 朋友经常临时约你，而你习惯提前规划，你会？',
        dimension: 'L',
        type: 'single',
        options: [
          { value: '5', label: '感到不适，希望对方提前' },
          { value: '4', label: '尽量调整，但会表达偏好' },
          { value: '3', label: '可以接受，但次数多了会烦' },
          { value: '2', label: '随叫随到' },
          { value: '1', label: '无所谓' }
        ]
      },
      // 维度五：情感支持 (E)
      {
        text: 'E1. 你希望朋友在你情绪低落时扮演什么角色？（可多选，最多选5项）',
        dimension: 'E',
        type: 'multiple',
        options: [
          { value: '耐心倾听者', label: '耐心倾听者' },
          { value: '理性分析者', label: '理性分析者' },
          { value: '幽默逗乐者', label: '幽默逗乐者' },
          { value: '陪伴左右者', label: '陪伴左右者' },
          { value: '给予实际帮助者', label: '给予实际帮助者' }
        ]
      },
      {
        text: 'E2. 你向朋友倾诉私事的频率？',
        dimension: 'E',
        type: 'single',
        options: [
          { value: '5', label: '经常，几乎无话不谈' },
          { value: '4', label: '偶尔，看情况' },
          { value: '3', label: '很少，只聊表面' },
          { value: '2', label: '几乎不' },
          { value: '1', label: '从不' }
        ]
      },
      {
        text: 'E3. 当朋友向你倾诉烦恼时，你通常？',
        dimension: 'E',
        type: 'single',
        options: [
          { value: '5', label: '耐心倾听，给予情感支持' },
          { value: '4', label: '帮忙分析问题，给建议' },
          { value: '3', label: '听但不太会回应' },
          { value: '2', label: '转移话题' },
          { value: '1', label: '感到不耐烦' }
        ]
      },
      {
        text: 'E4. 你希望朋友间的支持是？',
        dimension: 'E',
        type: 'single',
        options: [
          { value: '5', label: '双向的，互相依赖' },
          { value: '4', label: '我多付出一些也可以' },
          { value: '3', label: '对方多付出一些' },
          { value: '2', label: '各自独立，互不干涉' },
          { value: '1', label: '不需要支持' }
        ]
      },
      // 维度六：成长动力 (G)
      {
        text: 'G1. 你希望和朋友一起做哪些能提升自己的事？（可多选，最多选5项）',
        dimension: 'G',
        type: 'multiple',
        options: [
          { value: '一起学习新技能', label: '一起学习新技能' },
          { value: '一起读书讨论', label: '一起读书讨论' },
          { value: '一起健身锻炼', label: '一起健身锻炼' },
          { value: '一起参加培训讲座', label: '一起参加培训讲座' },
          { value: '一起创业搞项目', label: '一起创业搞项目' },
          { value: '一起旅行探索', label: '一起旅行探索' }
        ]
      },
      {
        text: 'G2. 你希望朋友在个人成长方面？',
        dimension: 'G',
        type: 'single',
        options: [
          { value: '5', label: '能带动我进步' },
          { value: '4', label: '能互相激励' },
          { value: '3', label: '能各自努力，偶尔交流' },
          { value: '2', label: '无所谓，不关心' },
          { value: '1', label: '不希望朋友太卷' }
        ]
      },
      {
        text: 'G3. 如果你在学习新事物，你希望朋友？',
        dimension: 'G',
        type: 'single',
        options: [
          { value: '5', label: '能和我一起学' },
          { value: '4', label: '能给我建议' },
          { value: '3', label: '能听我分享' },
          { value: '2', label: '不干涉就行' },
          { value: '1', label: '没想过' }
        ]
      },
      {
        text: 'G4. 对于未来规划，你希望朋友？',
        dimension: 'G',
        type: 'single',
        options: [
          { value: '5', label: '有相似的目标，可以一起奋斗' },
          { value: '4', label: '能理解并支持我的目标' },
          { value: '3', label: '无所谓，各自发展' },
          { value: '2', label: '不太关心对方目标' },
          { value: '1', label: '完全不在意' }
        ]
      }
    ];
  }
  // 初始化答案数组
  answers.value = questions.value.map(question => {
    return question.type === 'multiple' ? [] : '';
  });
};

const loadSavedAnswers = async () => {
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user || !selectedIntent.value) return;
  
  try {
    const response = await axios.get('http://localhost:5000/api/intent/' + user.id);
    if (response.data.status === 'success') {
      const intents = response.data.data.intents;
      const savedIntent = intents.find(intent => intent.intent_type === selectedIntent.value);
      
      if (savedIntent && savedIntent.answers) {
        const savedAnswers = savedIntent.answers.split(',');
        // 确保答案数组长度与问题数量匹配
        for (let i = 0; i < questions.value.length; i++) {
          if (i < savedAnswers.length) {
            const question = questions.value[i];
            if (question && question.type === 'multiple') {
              // 多选题答案，使用|分隔多个值
              if (savedAnswers[i] && savedAnswers[i] !== '') {
                answers.value[i] = savedAnswers[i].split('|');
              } else {
                answers.value[i] = [];
              }
            } else {
              // 单选题答案
              answers.value[i] = savedAnswers[i];
            }
          }
        }
        console.log('已加载的答案:', answers.value);
      }
    }
  } catch (error) {
    console.error('加载已保存答案失败:', error);
  }
};

const calculateIntentScores = () => {
  const scores = {};
  
  if (selectedIntent.value === '伴侣') {
    // 1. 安全联结维度（S）
    let S1 = parseInt(answers.value[0]) || 0;
    let S2 = parseInt(answers.value[1]) || 0;
    let S3 = parseInt(answers.value[2]) || 0;
    let S4 = parseInt(answers.value[3]) || 0;
    let S5 = parseInt(answers.value[4]) || 0;
    const S = (S1 + S2 + S3 + S4 + S5) / 5;
    scores.S = Math.round(S * 10) / 10;
    
    // 2. 互动模式维度（I）
    let I1 = parseInt(answers.value[5]) || 0;
    let I2 = parseInt(answers.value[6]) || 0;
    let I3 = parseInt(answers.value[7]) || 0;
    let I4 = parseInt(answers.value[8]) || 0;
    let I5 = parseInt(answers.value[9]) || 0;
    let I6 = parseInt(answers.value[10]) || 0;
    const I = (I1 + I2 + I3 + I4 + I5 + I6) / 6;
    scores.I = Math.round(I * 10) / 10;
    
    // 3. 现实坐标维度（R）
    let R1 = parseInt(answers.value[11]) || 0;
    let R2 = parseInt(answers.value[12]) || 0;
    let R3 = parseInt(answers.value[13]) || 0;
    let R4 = parseInt(answers.value[14]) || 0;
    let R5 = parseInt(answers.value[15]) || 0;
    const R = (R1 + R2 + R3 + R4 + R5) / 5;
    scores.R = Math.round(R * 10) / 10;
    
    // 4. 意义系统维度（M）
    let M1 = parseInt(answers.value[16]) || 0;
    let M2 = parseInt(answers.value[17]) || 0;
    let M3 = parseInt(answers.value[18]) || 0;
    let M4 = parseInt(answers.value[19]) || 0;
    let M5 = parseInt(answers.value[20]) || 0;
    const M = (M1 + M2 + M3 + M4 + M5) / 5;
    scores.M = Math.round(M * 10) / 10;
    
    // 5. 动力发展维度（D）
    let D1 = parseInt(answers.value[21]) || 0;
    let D2 = parseInt(answers.value[22]) || 0;
    let D3 = parseInt(answers.value[23]) || 0;
    let D4 = parseInt(answers.value[24]) || 0;
    let D5 = parseInt(answers.value[25]) || 0;
    const D = (D1 + D2 + D3 + D4 + D5) / 5;
    scores.D = Math.round(D * 10) / 10;
    
    // 6. 日常系统维度（E）
    let E1 = parseInt(answers.value[26]) || 0;
    let E2 = parseInt(answers.value[27]) || 0;
    let E3 = parseInt(answers.value[28]) || 0;
    let E4 = parseInt(answers.value[29]) || 0;
    let E5 = parseInt(answers.value[30]) || 0;
    const E = (E1 + E2 + E3 + E4 + E5) / 5;
    scores.E = Math.round(E * 10) / 10;
    
    // 7. 灵魂共振维度（N）
    let N1 = parseInt(answers.value[31]) || 0;
    let N2 = parseInt(answers.value[32]) || 0;
    let N3 = parseInt(answers.value[33]) || 0;
    let N4 = parseInt(answers.value[34]) || 0;
    let N5 = parseInt(answers.value[35]) || 0;
    const N = (N1 + N2 + N3 + N4 + N5) / 5;
    scores.N = Math.round(N * 10) / 10;
    
    // 计算总得分
    const total = (S + I + R + M + D + E + N) / 7;
    scores.overall = Math.round(total * 10) / 10;
  } else if (selectedIntent.value === '志趣相投的朋友') {
    // 朋友意向的得分计算
    // 维度一：兴趣共鸣 (I)
    let I1_raw = Array.isArray(answers.value[0]) ? answers.value[0].length : 0;
    I1_raw = Math.min(I1_raw, 5); // 最多选5项
    let I1 = 1 + (I1_raw / 5) * 4;
    let I2 = parseInt(answers.value[1]) || 0;
    let I3 = parseInt(answers.value[2]) || 0;
    let I4 = parseInt(answers.value[3]) || 0;
    const I = (I1 + I2 + I3 + I4) / 4;
    scores.I = Math.round(I * 10) / 10;
    
    // 维度二：价值观契合 (V)
    let V1_raw = Array.isArray(answers.value[4]) ? answers.value[4].length : 0;
    V1_raw = Math.min(V1_raw, 5); // 最多选5项
    let V1 = 1 + (V1_raw / 5) * 4;
    let V2 = parseInt(answers.value[5]) || 0;
    let V3 = parseInt(answers.value[6]) || 0;
    let V4 = parseInt(answers.value[7]) || 0;
    const V = (V1 + V2 + V3 + V4) / 4;
    scores.V = Math.round(V * 10) / 10;
    
    // 维度三：性格相容 (P)
    let P1_raw = Array.isArray(answers.value[8]) ? answers.value[8].length : 0;
    P1_raw = Math.min(P1_raw, 3); // 最多选3项
    let P1 = 1 + (P1_raw / 3) * 4;
    let P2 = parseInt(answers.value[9]) || 0;
    let P3 = parseInt(answers.value[10]) || 0;
    let P4 = parseInt(answers.value[11]) || 0;
    const P = (P1 + P2 + P3 + P4) / 4;
    scores.P = Math.round(P * 10) / 10;
    
    // 维度四：生活节奏 (L)
    let L1 = parseInt(answers.value[12]) || 0;
    let L2_raw = Array.isArray(answers.value[13]) ? answers.value[13].length : 0;
    L2_raw = Math.min(L2_raw, 5); // 最多选5项
    let L2 = 1 + (L2_raw / 5) * 4;
    let L3 = parseInt(answers.value[14]) || 0;
    let L4 = parseInt(answers.value[15]) || 0;
    const L = (L1 + L2 + L3 + L4) / 4;
    scores.L = Math.round(L * 10) / 10;
    
    // 维度五：情感支持 (E)
    let E1_raw = Array.isArray(answers.value[16]) ? answers.value[16].length : 0;
    E1_raw = Math.min(E1_raw, 5); // 最多选5项
    let E1 = 1 + (E1_raw / 5) * 4;
    let E2 = parseInt(answers.value[17]) || 0;
    let E3 = parseInt(answers.value[18]) || 0;
    let E4 = parseInt(answers.value[19]) || 0;
    const E = (E1 + E2 + E3 + E4) / 4;
    scores.E = Math.round(E * 10) / 10;
    
    // 维度六：成长动力 (G)
    let G1_raw = Array.isArray(answers.value[20]) ? answers.value[20].length : 0;
    G1_raw = Math.min(G1_raw, 5); // 最多选5项
    let G1 = 1 + (G1_raw / 5) * 4;
    let G2 = parseInt(answers.value[21]) || 0;
    let G3 = parseInt(answers.value[22]) || 0;
    let G4 = parseInt(answers.value[23]) || 0;
    const G = (G1 + G2 + G3 + G4) / 4;
    scores.G = Math.round(G * 10) / 10;
    
    // 计算总得分
    const total = (I + V + P + L + E + G) / 6;
    scores.overall = Math.round(total * 10) / 10;
  }
  
  return scores;
};

const submitAnswers = async () => {
  try {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
      router.push('/login');
      return;
    }
    
    // 计算意向得分
    const intentScores = calculateIntentScores();
    
    console.log('用户信息:', user);
    console.log('匹配意向:', selectedIntent.value);
    console.log('答案:', answers.value);
    console.log('意向得分:', intentScores);
    
    // 处理答案格式，多选题使用|分隔
    const formattedAnswers = answers.value.map(answer => {
      return Array.isArray(answer) ? answer.join('|') : answer;
    });
    
    const intentData = {
      user_id: user.id,
      intent_type: selectedIntent.value,
      answers: formattedAnswers.join(','),
      scores: JSON.stringify(intentScores)
    };
    
    console.log('提交的数据:', intentData);
    
    const response = await axios.post('http://localhost:5000/api/intent', intentData);
    console.log('API响应:', response.data);
    
    if (response.data.status === 'success') {
      // 保存成功后，更新已完成的意向列表
      if (!completedIntents.value.includes(selectedIntent.value)) {
        completedIntents.value.push(selectedIntent.value);
      }
      // 保存意向完成状态
      localStorage.setItem('intent_completed', 'true');
      alert('匹配意向保存成功！');
      // 导航到聊天广场
      router.push('/square');
    } else {
      alert('保存失败：' + (response.data.message || '未知错误'));
    }
  } catch (error) {
    console.error('保存匹配意向失败:', error);
    alert('保存失败，请稍后重试。错误信息：' + error.message);
  }
};

const goToSquare = () => {
  router.push('/square');
};
</script>

<style scoped>
.intent-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: transparent
}

.glass-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  max-width: 800px;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 28px;
}

h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 24px;
}

/* 意向选择样式 */
.intent-selection {
  margin-top: 20px;
}

.intent-options {
  display: flex;
  gap: 30px;
  justify-content: center;
  flex-wrap: wrap;
}

.intent-option {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 15px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
  min-width: 250px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.intent-option:hover {
  background: rgba(255, 255, 255, 0.5);
  transform: translateY(-10px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.intent-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.intent-option h3 {
  margin-bottom: 10px;
  color: #333;
  font-size: 1.5rem;
}

.intent-option p {
  color: #666;
  line-height: 1.5;
}

/* 答题界面样式 */
.intent-questions {
  margin-top: 20px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

select {
  width: 100%;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(5px);
  font-size: 16px;
  transition: all 0.3s ease;
}

select:focus {
  outline: none;
  border-color: #6a11cb;
  box-shadow: 0 0 0 3px rgba(106, 17, 203, 0.2);
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
  margin-top: 30px;
}

.intent-hint {
  text-align: center;
  margin-bottom: 30px;
  color: #666;
  font-size: 14px;
}

.intent-footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.intent-footer h3 {
  text-align: center;
  margin-bottom: 15px;
  color: #333;
  font-size: 18px;
}

.completed-intent-list {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.completed-intent {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.btn-continue {
  display: block;
  width: 200px;
  margin: 0 auto;
  padding: 12px;
  background: linear-gradient(45deg, #10B981, #059669);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-continue:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.form-actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.btn-back {
  flex: 1;
  padding: 15px;
  background: rgba(255, 255, 255, 0.2);
  color: #333;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.btn-submit {
  flex: 1;
  padding: 15px;
  background: linear-gradient(45deg, #6a11cb, #2575fc);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(106, 17, 203, 0.4);
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
  
  .intent-options {
    flex-direction: column;
  }
  
  .intent-option {
    width: 100%;
  }
  
  .form-group {
    margin-bottom: 15px;
  }
  
  input, select, textarea {
    padding: 12px;
    font-size: 14px;
  }
  
  .checkbox-group {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .radio-group label {
    font-size: 14px;
    padding: 8px 12px;
  }
  
  .btn-submit,
  .btn-back,
  .btn-continue {
    padding: 12px;
    font-size: 14px;
  }
  
  .intent-footer {
    margin-top: 30px;
  }
  
  .completed-intent-list {
    flex-wrap: wrap;
  }
  
  .completed-intent {
    margin: 5px;
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
  
  .form-group {
    margin-bottom: 12px;
  }
  
  input, select, textarea {
    padding: 10px;
    font-size: 13px;
  }
  
  .checkbox-group {
    grid-template-columns: 1fr;
  }
  
  .radio-group label {
    font-size: 13px;
    padding: 6px 10px;
  }
  
  .btn-submit,
  .btn-back,
  .btn-continue {
    padding: 10px;
    font-size: 13px;
  }
  
  .intent-footer {
    margin-top: 20px;
  }
}

/* 单选按钮组样式 */
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 10px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.radio-option:hover {
  background: rgba(255, 255, 255, 0.2);
}

.radio-option input[type="radio"] {
  width: auto;
  margin: 0;
}

/* 复选框组样式 */
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 10px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.checkbox-option:hover {
  background: rgba(255, 255, 255, 0.2);
}

.checkbox-option input[type="checkbox"] {
  width: auto;
  margin: 0;
}

/* 排序题样式 */
.ranking-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ranking-option {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.ranking-option:hover {
  background: rgba(255, 255, 255, 0.2);
}

.ranking-select {
  width: 120px;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(5px);
  font-size: 14px;
}

/* 提示文字样式 */
.hint {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
  font-style: italic;
}

@media (max-width: 768px) {
  .glass-card {
    padding: 20px;
  }
  
  h1 {
    font-size: 24px;
  }
  
  h2 {
    font-size: 20px;
  }
  
  .intent-options {
    flex-direction: column;
    align-items: center;
  }
  
  .intent-option {
    width: 100%;
    max-width: 300px;
  }
  
  .ranking-option {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .ranking-select {
    width: 100%;
  }
}
</style>