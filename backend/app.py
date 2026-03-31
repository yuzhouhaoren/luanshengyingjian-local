from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
import base64
import time
import uuid

app = Flask(__name__)

# 启用CORS 跨域资源共享
CORS(app, origins=['http://localhost:5173', 'http://localhost:5174', 'http://localhost:5175', 'http://localhost:5176']) 

# 数据库配置
# 使用SQLite数据库

# 头像存储目录
AVATAR_DIR = 'avatars'
os.makedirs(AVATAR_DIR, exist_ok=True)

# 设置静态文件目录
@app.route('/')
def index():
    return send_from_directory('dist', 'index.html')

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory('dist', path)

# 数据库连接
def get_db():
    # SQLite连接
    conn = sqlite3.connect('dating.db', timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

# 数据库上下文管理器
from contextlib import contextmanager

@contextmanager
def get_db_context():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# 初始化数据库
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        location TEXT,
        occupation TEXT,
        sexual_orientation TEXT,
        hobbies TEXT,
        personality TEXT,
        communication_style TEXT,
        ideal_partner TEXT,
        chat_habits TEXT,
        carrp_answers TEXT,
        nri_answers TEXT,
        profile_scores TEXT,
        avatar TEXT,
        in_partner_pool BOOLEAN DEFAULT false,
        in_friend_pool BOOLEAN DEFAULT false
    )
    ''')
    
    # 创建聊天表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        chat_id TEXT,
        sender TEXT,
        message TEXT,
        timestamp TEXT,
        sender_type TEXT DEFAULT 'user'
    )
    ''')
    
    # 创建用户意向表（用户发送的请求）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_intents (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        intent_type TEXT,
        answers TEXT
    )
    ''')
    
    # 创建匹配结果表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS match_results (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        matched_user_id TEXT,
        matched_user_name TEXT,
        match_score REAL,
        intent_type TEXT,
        email TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建意向请求表（用户收到的请求）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS intent_requests (
        id TEXT PRIMARY KEY,
        from_user_id TEXT,
        to_user_id TEXT,
        from_user_name TEXT,
        message TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建 AI 机器人表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bots (
        id TEXT PRIMARY KEY,
        name TEXT,
        avatar TEXT,
        personality TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 插入默认 AI 机器人数据
    cursor.execute('SELECT COUNT(*) FROM bots')
    if cursor.fetchone()[0] == 0:
        default_bots = [
            {
                'id': 'bot_1',
                'name': '开心果',
                'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=friendly%20chatbot%20avatar&image_size=square',
                'personality': '开朗活泼，喜欢讲笑话，总是能让你开心',
                'description': '一个乐观向上的聊天伙伴，擅长讲笑话和分享有趣的故事'
            },
            {
                'id': 'bot_2',
                'name': '思考者',
                'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=thoughtful%20chatbot%20avatar&image_size=square',
                'personality': '深沉思考，善于分析问题，给你理性的建议',
                'description': '一个善于思考的聊天伙伴，擅长分析问题和提供理性建议'
            },
            {
                'id': 'bot_3',
                'name': '冒险家',
                'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=adventurous%20chatbot%20avatar&image_size=square',
                'personality': '热爱冒险，充满好奇心，喜欢探索新事物',
                'description': '一个充满冒险精神的聊天伙伴，喜欢分享探险故事和新发现'
            }
        ]
        for bot in default_bots:
            cursor.execute('''
            INSERT INTO bots (id, name, avatar, personality, description)
            VALUES (?, ?, ?, ?, ?)
            ''', (bot['id'], bot['name'], bot['avatar'], bot['personality'], bot['description']))
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# 健康检查
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute('SELECT * FROM users WHERE username = ?', (data.get('username'),))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': '用户名已存在'})
            
            # 检查邮箱是否已存在
            cursor.execute('SELECT * FROM users WHERE email = ?', (data.get('email'),))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': '邮箱已存在'})
            
            # 生成用户ID
            import uuid
            user_id = f"user_{uuid.uuid4().hex[:8]}"
            
            # 插入用户数据
            cursor.execute('''
            INSERT INTO users (id, username, email, password)
            VALUES (?, ?, ?, ?)
            ''', (user_id, data.get('username'), data.get('email'), data.get('password')))
        
        return jsonify({'status': 'success', 'user_id': user_id, 'username': data.get('username'), 'email': data.get('email')})
    except sqlite3.OperationalError as e:
        if 'locked' in str(e):
            return jsonify({'status': 'error', 'message': '数据库繁忙，请稍后重试'})
        raise e

# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找用户
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', 
                  (data.get('email'), data.get('password')))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return jsonify({'status': 'success', 'user_id': user['id'], 'username': user['username'], 'email': user['email']})
    else:
        return jsonify({'status': 'error', 'message': '邮箱或密码错误'})

# 提交用户画像
@app.route('/api/profile', methods=['POST'])
def submit_profile():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找用户
    cursor.execute('SELECT * FROM users WHERE id = ?', (data.get('user_id'),))
    user = cursor.fetchone()
    
    if user:
        # 计算个人画像得分
        profile_scores = {}
        try:
            if data.get('carrp_answers'):
                carrp_answers = data.get('carrp_answers').split(',')
                if len(carrp_answers) == 11:
                    # 处理反向计分题
                    processed_answers = []
                    for i, answer in enumerate(carrp_answers):
                        if i == 6:  # 第7题是反向计分题
                            processed_answers.append(6 - int(answer))
                        else:
                            processed_answers.append(int(answer))
                    
                    # 计算各维度得分
                    E = (processed_answers[0] + processed_answers[5] + processed_answers[6]) / 3
                    O = (processed_answers[1] + processed_answers[7]) / 2
                    C = (processed_answers[2] + processed_answers[9]) / 2
                    A = (processed_answers[4] + processed_answers[10]) / 2
                    N = (processed_answers[3] + processed_answers[8]) / 2
                    
                    # 计算自恋得分
                    narc_score = 0
                    if data.get('nri_answers'):
                        nri_answers = data.get('nri_answers').split(',')
                        if len(nri_answers) == 10:
                            for answer in nri_answers:
                                narc_score += int(answer)
                        narc_score = narc_score / 10
                    
                    profile_scores = {
                        'extraversion': round(E, 1),
                        'openness': round(O, 1),
                        'conscientiousness': round(C, 1),
                        'agreeableness': round(A, 1),
                        'neuroticism': round(N, 1),
                        'narcissism': round(narc_score, 1)
                    }
        except Exception as e:
            print(f"计算个人画像得分时出错: {e}")
            profile_scores = {
                'extraversion': 0,
                'openness': 0,
                'conscientiousness': 0,
                'agreeableness': 0,
                'neuroticism': 0,
                'narcissism': 0
            }
        
        # 更新用户画像
        cursor.execute('''
        UPDATE users SET age = ?, gender = ?, occupation = ?, sexual_orientation = ?, hobbies = ?, 
        personality = ?, communication_style = ?, ideal_partner = ?, chat_habits = ?, 
        carrp_answers = ?, nri_answers = ?, profile_scores = ?, avatar = ?
        WHERE id = ?
        ''', (data.get('age'), data.get('gender'), data.get('occupation'), data.get('sexual_orientation'),
              data.get('hobbies'), data.get('personality'), 
              data.get('communication_style'), data.get('ideal_partner'), 
              data.get('chat_habits'), data.get('carrp_answers'), 
              data.get('nri_answers'), json.dumps(profile_scores), data.get('avatar'), data.get('user_id')))
        
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'user_id': data.get('user_id'), 'profile_scores': profile_scores})
    else:
        conn.close()
        return jsonify({'status': 'error', 'message': '用户不存在'})

# 获取用户画像
@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找用户
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        profile = dict(user)
        # 解析profile_scores为JSON对象
        if profile.get('profile_scores'):
            try:
                profile['profile_scores'] = json.loads(profile['profile_scores'])
            except:
                profile['profile_scores'] = {}
        return jsonify({'status': 'success', 'profile': profile})
    else:
        return jsonify({'status': 'error', 'message': '用户不存在'})

# 上传头像
@app.route('/api/avatar/upload', methods=['POST'])
def upload_avatar():
    # 从表单获取文件
    if 'avatar' not in request.files:
        return jsonify({'status': 'error', 'message': '缺少头像文件'})
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'})
    
    # 从请求中获取用户ID
    user_id = request.form.get('user_id')
    if not user_id:
        # 尝试从本地存储获取用户ID（临时解决方案）
        # 实际项目中应该从认证token中获取
        return jsonify({'status': 'error', 'message': '缺少用户ID'})
    
    try:
        # 生成头像文件名
        avatar_filename = f"{user_id}_avatar.{file.filename.rsplit('.', 1)[1].lower()}"
        avatar_path = os.path.join(AVATAR_DIR, avatar_filename)
        
        # 保存头像
        file.save(avatar_path)
        
        # 更新用户头像路径
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_filename, user_id))
        
        conn.commit()
        conn.close()
        
        # 生成头像URL
        avatar_url = f'/avatars/{avatar_filename}'
        
        return jsonify({'status': 'success', 'avatar_path': avatar_url})
    except Exception as e:
        print(f"上传头像失败: {e}")
        return jsonify({'status': 'error', 'message': '上传头像失败'})

# 静态头像文件服务
@app.route('/avatars/<filename>')
def serve_avatar(filename):
    return send_from_directory(AVATAR_DIR, filename)

# 匹配要用到的api。里面的内容是乱的别管
@app.route('/api/match/<user_id>', methods=['GET'])
def get_user_matches(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找所有用户，排除当前用户
    cursor.execute('SELECT * FROM users WHERE id != ?', (user_id,))
    users = cursor.fetchall()
    
    conn.close()
    
    # 转换为字典列表
    matches = []
    for user in users:
        match = dict(user)
        if match.get('hobbies'):
            match['hobbies'] = json.loads(match['hobbies'])
        matches.append(match)
    
    return jsonify({'status': 'success', 'matches': matches})

# 获取聊天广场
@app.route('/api/chat/square', methods=['GET'])
def get_chat_square():
    """获取聊天广场，返回可用的 AI 机器人列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 从数据库获取机器人列表
    cursor.execute('SELECT id, name, avatar FROM bots')
    bots = cursor.fetchall()
    
    conn.close()
    
    # 转换为字典列表
    bot_list = []
    for bot in bots:
        bot_list.append({
            "id": bot['id'],
            "name": bot['name'],
            "avatar": bot['avatar']
        })
    
    return jsonify({'status': 'success', 'bots': bot_list})

# 发送聊天消息
@app.route('/api/chat', methods=['POST'])
def send_message():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    # 生成消息ID
    cursor.execute('SELECT COUNT(*) FROM chats')
    count = cursor.fetchone()[0]
    message_id = f"msg_{count + 1}"
    
    # 插入消息
    cursor.execute('''
    INSERT INTO chats (id, chat_id, sender, message, timestamp, sender_type)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (message_id, data.get('chat_id'), data.get('sender'), 
          data.get('message'), data.get('timestamp', 'now'), data.get('sender_type', 'user')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'chat_id': data.get('chat_id')})

# 获取聊天历史
@app.route('/api/chat/history/<chat_id>', methods=['GET'])
def get_chat_history(chat_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找聊天历史
    cursor.execute('SELECT * FROM chats WHERE chat_id = ? ORDER BY timestamp', (chat_id,))
    messages = cursor.fetchall()
    
    conn.close()
    
    # 转换为字典列表
    history = []
    for msg in messages:
        history.append({
            'sender': msg['sender'],
            'message': msg['message'],
            'timestamp': msg['timestamp'],
            'sender_type': msg.get('sender_type', 'user')
        })
    
    return jsonify({'status': 'success', 'history': history})

# 获取所有 AI 机器人
@app.route('/api/bots', methods=['GET'])
def get_bots():
    """获取所有 AI 机器人信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 从数据库获取所有机器人
    cursor.execute('SELECT * FROM bots')
    bots = cursor.fetchall()
    
    conn.close()
    
    # 转换为字典列表
    bot_list = []
    for bot in bots:
        bot_list.append({
            'id': bot['id'],
            'name': bot['name'],
            'avatar': bot['avatar'],
            'personality': bot['personality'],
            'description': bot['description']
        })
    
    return jsonify({'status': 'success', 'bots': bot_list})

# 获取特定 AI 机器人
@app.route('/api/bot/<bot_id>', methods=['GET'])
def get_bot(bot_id):
    """获取特定 AI 机器人的详细信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 从数据库获取指定机器人
    cursor.execute('SELECT * FROM bots WHERE id = ?', (bot_id,))
    bot = cursor.fetchone()
    
    conn.close()
    
    if bot:
        bot_info = {
            'id': bot['id'],
            'name': bot['name'],
            'avatar': bot['avatar'],
            'personality': bot['personality'],
            'description': bot['description']
        }
        return jsonify({'status': 'success', 'bot': bot_info})
    else:
        return jsonify({'status': 'error', 'message': '机器人不存在'})

# 获取匹配统计数据
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    # 计算总用户数
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # 计算匹配成功对数（实际项目中应该从数据库中获取）
    # 暂时设置为0，因为还没有真实的匹配数据
    matched_pairs = 0
    
    # 每日匹配数据（实际项目中应该从数据库中获取）
    # 暂时设置为全0，因为还没有真实的匹配数据
    daily_matches = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    conn.close()
    
    return jsonify({
        'status': 'success',
        'data': {
            'total_users': total_users,
            'matched_pairs': matched_pairs,
            'daily_matches': daily_matches
        }
    })

# 提交匹配意向
@app.route('/api/intent', methods=['POST'])
def submit_intent():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    # 生成意向ID
    cursor.execute('SELECT COUNT(*) FROM user_intents')
    count = cursor.fetchone()[0]
    intent_id = f"intent_{count + 1}"
    
    # 检查用户是否已有相同类型的意向
    cursor.execute('SELECT * FROM user_intents WHERE user_id = ? AND intent_type = ?', 
                  (data.get('user_id'), data.get('intent_type')))
    existing_intent = cursor.fetchone()
    
    if existing_intent:
        # 更新已有意向
        cursor.execute('''
        UPDATE user_intents SET answers = ?
        WHERE user_id = ? AND intent_type = ?
        ''', (data.get('answers'), data.get('user_id'), data.get('intent_type')))
    else:
        # 插入新意向
        cursor.execute('''
        INSERT INTO user_intents (id, user_id, intent_type, answers)
        VALUES (?, ?, ?, ?)
        ''', (intent_id, data.get('user_id'), data.get('intent_type'), data.get('answers')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': '匹配意向保存成功'})

# 获取用户的所有匹配意向
@app.route('/api/intent/<user_id>', methods=['GET'])
def get_user_intents(user_id):
    """获取用户的所有匹配意向"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找用户的所有意向
    cursor.execute('SELECT * FROM user_intents WHERE user_id = ?', (user_id,))
    intents = cursor.fetchall()
    
    conn.close()
    
    # 转换为字典列表
    intent_list = []
    for intent in intents:
        intent_dict = dict(intent)
        intent_list.append(intent_dict)
    
    return jsonify({
        'status': 'success',
        'data': {
            'intents': intent_list
        }
    })



# 生成广场帖子API（核心服务）
@app.route('/api/square/posts', methods=['GET'])
def get_square_posts():
    """获取基于用户画像生成的广场帖子"""
    # 这里留作帖子生成的实现
    # 实际项目中，会根据用户画像和其他用户的画像生成帖子
    
    # 模拟帖子数据
    posts = [
        {
            "id": "post_1",
            "title": "周末一起去爬山吗？",
            "content": "最近天气很好，想找个志同道合的朋友一起去爬山，有没有兴趣的？",
            "author": "用户1",
            "avatar": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=friendly%20user%20avatar&image_size=square",
            "image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=mountain%20hiking%20scenery&image_size=landscape_16_9"
        },
        {
            "id": "post_2",
            "title": "推荐一本好书",
            "content": "最近读了一本非常棒的书，推荐给大家，关于人际关系的建立和维护...",
            "author": "用户2",
            "avatar": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=intellectual%20user%20avatar&image_size=square",
            "image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=book%20reading%20scene&image_size=landscape_16_9"
        }
    ]
    
    return jsonify({
        'status': 'success',
        'data': {
            'posts': posts
        }
    })

# 生成帖子的文本与图片API
@app.route('/api/posts/generate', methods=['POST'])
def generate_post():
    """生成帖子的文本与图片"""
    data = request.json
    user_id = data.get('user_id')
    
    # 这里留作帖子生成的实现
    # 实际项目中，会根据用户画像生成帖子文本和图片
    
    # 模拟生成的帖子数据
    generated_post = {
        "id": f"post_{int(time.time())}",
        "title": "我的新动态",
        "content": "这是一条生成的帖子内容，分享我的生活和想法。",
        "image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=random%20life%20scene&image_size=landscape_16_9"
    }
    
    return jsonify({
        'status': 'success',
        'data': generated_post
    })

# 匹配池匹配API
@app.route('/api/match/pool', methods=['POST'])
def match_pool():
    """匹配池匹配，给特定用户发匹配结果"""
    data = request.json
    user_id = data.get('user_id')
    
    # 这里留作匹配算法的实现
    # 实际项目中，会根据用户画像和匹配意向进行匹配
    
    # 模拟匹配结果
    match_results = [
        {
            "matched_user_id": "user_2",
            "matched_user_name": "用户2",
            "intent_type": "朋友",
            "email": "user2@example.com",
            "match_score": 0.92
        },
        {
            "matched_user_id": "user_3",
            "matched_user_name": "用户3",
            "intent_type": "伴侣",
            "email": "user3@example.com",
            "match_score": 0.85
        }
    ]
    
    # 保存匹配结果到数据库
    conn = get_db()
    cursor = conn.cursor()
    
    for match in match_results:
        # 为当前用户创建匹配结果
        cursor.execute('''
            INSERT INTO match_results (user_id, matched_user_id, matched_user_name, match_score, intent_type, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, match['matched_user_id'], match['matched_user_name'], match['match_score'], match['intent_type'], match['email']))
        
        # 为匹配用户创建匹配结果（确保双向平等）
        # 获取当前用户信息
        cursor.execute('SELECT name, email FROM users WHERE id = ?', (user_id,))
        current_user = cursor.fetchone()
        current_user_name = current_user['name'] if current_user and current_user['name'] else '未知用户'
        current_user_email = current_user['email'] if current_user else ''
        
        cursor.execute('''
            INSERT INTO match_results (user_id, matched_user_id, matched_user_name, match_score, intent_type, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (match['matched_user_id'], user_id, current_user_name, match['match_score'], match['intent_type'], current_user_email))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'status': 'success',
        'data': {
            'matches': match_results
        }
    })

# 获取用户列表API
@app.route('/api/users', methods=['GET'])
def get_users():
    """获取所有用户列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找所有用户
    cursor.execute('SELECT id, username, name, age, gender, location FROM users')
    users = cursor.fetchall()
    
    conn.close()
    
    # 转换为字典列表
    user_list = []
    for user in users:
        user_dict = dict(user)
        user_list.append(user_dict)
    
    return jsonify({
        'status': 'success',
        'data': {
            'users': user_list
        }
    })

# 获取平台性格分布数据API
@app.route('/api/personality/stats', methods=['GET'])
def get_personality_stats():
    """获取平台用户性格分布数据"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找所有用户的profile_scores
    cursor.execute('SELECT profile_scores FROM users WHERE profile_scores IS NOT NULL')
    profiles = cursor.fetchall()
    
    conn.close()
    
    # 计算平均性格得分
    if not profiles:
        return jsonify({
            'status': 'success',
            'data': {
                'extraversion': 0,
                'openness': 0,
                'conscientiousness': 0,
                'agreeableness': 0,
                'neuroticism': 0,
                'narcissism': 0
            }
        })
    
    total = {
        'extraversion': 0,
        'openness': 0,
        'conscientiousness': 0,
        'agreeableness': 0,
        'neuroticism': 0,
        'narcissism': 0
    }
    count = 0
    
    for profile in profiles:
        try:
            # SQLite返回的是Row对象
            profile_scores = profile['profile_scores']
            scores = json.loads(profile_scores)
            for key in total:
                if key in scores:
                    total[key] += scores[key]
            count += 1
        except:
            pass
    
    # 计算平均值
    if count > 0:
        for key in total:
            total[key] = round(total[key] / count, 1)
    
    return jsonify({
        'status': 'success',
        'data': total
    })

# 获取用户的匹配结果
@app.route('/api/matches/<user_id>', methods=['GET'])
def get_matches(user_id):
    """获取用户的匹配结果"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT mr.*, u.name as matched_user_name
        FROM match_results mr
        LEFT JOIN users u ON mr.matched_user_id = u.id
        WHERE mr.user_id = ? AND mr.status = 'pending'
        ORDER BY mr.created_at DESC
    ''', (user_id,))
    
    matches = cursor.fetchall()
    conn.close()
    
    match_list = []
    for match in matches:
        match_dict = dict(match)
        match_list.append(match_dict)
    
    return jsonify({
        'status': 'success',
        'matches': match_list
    })

# 接受匹配
@app.route('/api/matches/accept', methods=['POST'])
def accept_match():
    """接受匹配"""
    data = request.json
    match_id = data.get('match_id')
    
    if not match_id:
        return jsonify({'status': 'error', 'message': '缺少匹配ID'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE match_results SET status = ? WHERE id = ?', ('accepted', match_id))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

# 拒绝匹配
@app.route('/api/matches/reject', methods=['POST'])
def reject_match():
    """拒绝匹配"""
    data = request.json
    match_id = data.get('match_id')
    
    if not match_id:
        return jsonify({'status': 'error', 'message': '缺少匹配ID'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE match_results SET status = ? WHERE id = ?', ('rejected', match_id))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

# 发送意向申请
@app.route('/api/intent-request/send', methods=['POST'])
def send_intent_request():
    """发送意向申请"""
    data = request.json
    from_user_id = data.get('from_user_id')
    to_user_id = data.get('to_user_id')
    message = data.get('message', '')
    
    if not from_user_id or not to_user_id:
        return jsonify({'status': 'error', 'message': '缺少用户ID'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取发送者姓名
    cursor.execute('SELECT name, username FROM users WHERE id = ?', (from_user_id,))
    from_user = cursor.fetchone()
    from_user_name = from_user['name'] if from_user and from_user['name'] else from_user['username'] if from_user else '未知用户'
    
    cursor.execute('''
        INSERT INTO intent_requests (from_user_id, to_user_id, from_user_name, message)
        VALUES (?, ?, ?, ?)
    ''', (from_user_id, to_user_id, from_user_name, message))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

# 获取用户的意向申请
@app.route('/api/intent-requests/<user_id>', methods=['GET'])
def get_intent_requests(user_id):
    """获取用户的意向申请"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM intent_requests
        WHERE to_user_id = ? AND status = 'pending'
        ORDER BY created_at DESC
    ''', (user_id,))
    
    requests = cursor.fetchall()
    conn.close()
    
    request_list = []
    for req in requests:
        req_dict = dict(req)
        request_list.append(req_dict)
    
    return jsonify({
        'status': 'success',
        'requests': request_list
    })

# 接受意向申请
@app.route('/api/intent-request/accept', methods=['POST'])
def accept_intent_request():
    """接受意向申请"""
    data = request.json
    request_id = data.get('request_id')
    
    if not request_id:
        return jsonify({'status': 'error', 'message': '缺少申请ID'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取意向申请的详细信息
    cursor.execute('SELECT * FROM intent_requests WHERE id = ?', (request_id,))
    request = cursor.fetchone()
    
    if request:
        # 转换为字典
        request_dict = dict(request)
        
        # 获取发送者的邮箱
        cursor.execute('SELECT email FROM users WHERE id = ?', (request_dict['from_user_id'],))
        from_user = cursor.fetchone()
        from_user_email = from_user['email'] if from_user else ''
        
        # 获取接收者的邮箱
        cursor.execute('SELECT email FROM users WHERE id = ?', (request_dict['to_user_id'],))
        to_user = cursor.fetchone()
        to_user_email = to_user['email'] if to_user else ''
        
        # 为接收者创建匹配结果
        cursor.execute('''
            INSERT INTO match_results (user_id, matched_user_id, matched_user_name, match_score, intent_type, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (request_dict['to_user_id'], request_dict['from_user_id'], request_dict['from_user_name'], 0.9, request_dict.get('intent_type', '朋友'), from_user_email))
        
        # 为发送者创建匹配结果
        cursor.execute('''
            INSERT INTO match_results (user_id, matched_user_id, matched_user_name, match_score, intent_type, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (request_dict['from_user_id'], request_dict['to_user_id'], request_dict.get('to_user_name', '未知用户'), 0.9, request_dict.get('intent_type', '朋友'), to_user_email))
    
    # 更新意向申请状态
    cursor.execute('UPDATE intent_requests SET status = ? WHERE id = ?', ('accepted', request_id))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

# 拒绝意向申请
@app.route('/api/intent-request/reject', methods=['POST'])
def reject_intent_request():
    """拒绝意向申请"""
    data = request.json
    request_id = data.get('request_id')
    
    if not request_id:
        return jsonify({'status': 'error', 'message': '缺少申请ID'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE intent_requests SET status = ? WHERE id = ?', ('rejected', request_id))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

# 获取未读消息数量
@app.route('/api/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    """获取用户的未读消息数量"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取待处理的匹配结果数量
    cursor.execute('SELECT COUNT(*) FROM match_results WHERE user_id = ? AND status = ?', (user_id, 'pending'))
    match_count = cursor.fetchone()[0]
    
    # 获取待处理的意向申请数量
    cursor.execute('SELECT COUNT(*) FROM intent_requests WHERE to_user_id = ? AND status = ?', (user_id, 'pending'))
    request_count = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'status': 'success',
        'data': {
            'match_count': match_count,
            'request_count': request_count,
            'total': match_count + request_count
        }
    })

# 注销账号
@app.route('/api/account/delete', methods=['POST'])
def delete_account():
    """注销账号"""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'status': 'error', 'message': '缺少用户ID'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 删除用户相关的所有数据
        # 删除匹配结果
        cursor.execute('DELETE FROM match_results WHERE user_id = ? OR matched_user_id = ?', (user_id, user_id))
        # 删除意向申请
        cursor.execute('DELETE FROM intent_requests WHERE from_user_id = ? OR to_user_id = ?', (user_id, user_id))
        # 删除用户数据
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)