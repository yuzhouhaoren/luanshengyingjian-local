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
        
        age INTEGER,
        gender TEXT,
        location TEXT,
        occupation TEXT,
        sexual_orientation TEXT,
        
       
        
        carrp_answers TEXT,  -- CARRP问卷答案
        nri_answers TEXT,     -- NRI问卷答案
        partner_intent_answers TEXT,  -- 伴侣意向答案
        friend_intent_answers TEXT,   -- 朋友意向答案
        profile_scores TEXT,  -- 个人画像分数（JSON格式）
        -- 个人画像维度：E(外向性)、O(开放性)、C(尽责性)、A(宜人性)、N(神经质)
        -- 伴侣意向维度：S(安全联结)、I(互动模式)、R(现实坐标)、M(意义系统)、D(动力发展)、E(日常系统)、N(灵魂共振)
        -- 朋友意向维度：I(兴趣共鸣)、V(价值观契合)、P(性格相容)、L(生活节奏)、E(情感支持)、G(成长动力)
        -- 示例：{"E":4.5,"O":3.8,"C":4.2,"A":3.9,"N":4.1,"intent_伴侣":{"S":4.5,"I":3.8,"R":4.2,"M":3.9,"D":4.1,"E":3.7,"N":4.0},"intent_志趣相投的朋友":{"I":4.3,"V":3.9,"P":4.1,"L":3.8,"E":4.0,"G":3.7}}
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
    
    # 创建用户发送的交友请求表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sent_friend_requests (
        id TEXT PRIMARY KEY,
        from_user_id TEXT,
        to_user_id TEXT,
        from_user_name TEXT,
        to_user_name TEXT,
        intent_type TEXT,
        message TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    # 创建用户收到的交友申请表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS received_friend_requests (
        id TEXT PRIMARY KEY,
        from_user_id TEXT,
        to_user_id TEXT,
        from_user_name TEXT,
        from_user_email TEXT,
        message TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 添加新字段（如果不存在）
    try:
        # 添加伴侣意向答案字段
        cursor.execute('ALTER TABLE users ADD COLUMN partner_intent_answers TEXT')
    except sqlite3.OperationalError:
        # 字段已存在，忽略错误
        pass
    
    try:
        # 添加朋友意向答案字段
        cursor.execute('ALTER TABLE users ADD COLUMN friend_intent_answers TEXT')
    except sqlite3.OperationalError:
        # 字段已存在，忽略错误
        pass
    
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
        UPDATE users SET age = ?, gender = ?, occupation = ?, sexual_orientation = ?, 
        carrp_answers = ?, nri_answers = ?, profile_scores = ?, avatar = ?
        WHERE id = ?
        ''', (data.get('age'), data.get('gender'), data.get('occupation'), data.get('sexual_orientation'),
              data.get('carrp_answers'), data.get('nri_answers'), json.dumps(profile_scores), data.get('avatar'), 
              data.get('user_id')))
        
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
        return jsonify({'status': 'error', 'message': '缺少用户ID'})
    
    try:
        # 生成唯一头像文件名，避免文件名冲突
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        avatar_filename = f"{user_id}_{int(time.time())}.{file_extension}"
        avatar_path = os.path.join(AVATAR_DIR, avatar_filename)
        
        # 保存头像
        file.save(avatar_path)
        
        # 更新用户头像路径
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_filename, user_id))
        
        conn.commit()
        conn.close()
        
        # 返回完整的头像URL
        avatar_url = f'http://localhost:5000/avatars/{avatar_filename}'
        
        return jsonify({'status': 'success', 'avatar_url': avatar_url, 'avatar_filename': avatar_filename})
    except Exception as e:
        print(f"上传头像失败: {e}")
        return jsonify({'status': 'error', 'message': '上传头像失败'})

# 静态头像文件服务
@app.route('/avatars/<filename>')
def serve_avatar(filename):
    return send_from_directory(AVATAR_DIR, filename)





# 发送广场聊天消息
@app.route('/api/square/chat', methods=['POST'])
def send_square_message():
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

# 计算匹配意向分数
def calculate_intent_scores(intent_type, answers_str):
    """计算匹配意向的维度分数"""
    scores = {}
    
    try:
        # 解析答案字符串
        answers = answers_str.split(',')
        
        if intent_type == '伴侣':
            # 伴侣意向的7个维度计算
            # 支持部分答案计算，只要有足够答案就计算对应维度
            
            # 1. 安全联结维度（S） - 需要5个答案
            if len(answers) >= 5:
                S1 = float(answers[0]) if answers[0] else 0
                S2 = float(answers[1]) if answers[1] else 0
                S3 = float(answers[2]) if answers[2] else 0
                S4 = float(answers[3]) if answers[3] else 0
                S5 = float(answers[4]) if answers[4] else 0
                S = (S1 + S2 + S3 + S4 + S5) / 5
                scores['S'] = round(S, 1)
            
            # 2. 互动模式维度（I） - 需要6个答案（从第6题开始）
            if len(answers) >= 11:
                I1 = float(answers[5]) if answers[5] else 0
                I2 = float(answers[6]) if answers[6] else 0
                I3 = float(answers[7]) if answers[7] else 0
                I4 = float(answers[8]) if answers[8] else 0
                I5 = float(answers[9]) if answers[9] else 0
                I6 = float(answers[10]) if answers[10] else 0
                I = (I1 + I2 + I3 + I4 + I5 + I6) / 6
                scores['I'] = round(I, 1)
            
            # 3. 现实坐标维度（R） - 需要5个答案（从第12题开始）
            if len(answers) >= 16:
                R1 = float(answers[11]) if answers[11] else 0
                R2 = float(answers[12]) if answers[12] else 0
                R3 = float(answers[13]) if answers[13] else 0
                R4 = float(answers[14]) if answers[14] else 0
                R5 = float(answers[15]) if answers[15] else 0
                R = (R1 + R2 + R3 + R4 + R5) / 5
                scores['R'] = round(R, 1)
            
            # 4. 意义系统维度（M） - 需要5个答案（从第17题开始）
            if len(answers) >= 21:
                M1 = float(answers[16]) if answers[16] else 0
                M2 = float(answers[17]) if answers[17] else 0
                M3 = float(answers[18]) if answers[18] else 0
                M4 = float(answers[19]) if answers[19] else 0
                M5 = float(answers[20]) if answers[20] else 0
                M = (M1 + M2 + M3 + M4 + M5) / 5
                scores['M'] = round(M, 1)
            
            # 5. 动力发展维度（D） - 需要5个答案（从第22题开始）
            if len(answers) >= 26:
                D1 = float(answers[21]) if answers[21] else 0
                D2 = float(answers[22]) if answers[22] else 0
                D3 = float(answers[23]) if answers[23] else 0
                D4 = float(answers[24]) if answers[24] else 0
                D5 = float(answers[25]) if answers[25] else 0
                D = (D1 + D2 + D3 + D4 + D5) / 5
                scores['D'] = round(D, 1)
            
            # 6. 日常系统维度（E） - 需要5个答案（从第27题开始）
            if len(answers) >= 31:
                E1 = float(answers[26]) if answers[26] else 0
                E2 = float(answers[27]) if answers[27] else 0
                E3 = float(answers[28]) if answers[28] else 0
                E4 = float(answers[29]) if answers[29] else 0
                E5 = float(answers[30]) if answers[30] else 0
                E = (E1 + E2 + E3 + E4 + E5) / 5
                scores['E'] = round(E, 1)
            
            # 7. 灵魂共振维度（N） - 需要5个答案（从第32题开始）
            if len(answers) >= 36:
                N1 = float(answers[31]) if answers[31] else 0
                N2 = float(answers[32]) if answers[32] else 0
                N3 = float(answers[33]) if answers[33] else 0
                N4 = float(answers[34]) if answers[34] else 0
                N5 = float(answers[35]) if answers[35] else 0
                N = (N1 + N2 + N3 + N4 + N5) / 5
                scores['N'] = round(N, 1)
            
            # 匹配意向分数是各维度得分，不计算总分
            # 移除overall字段，专注于各维度得分
            if 'overall' in scores:
                del scores['overall']
        
        elif intent_type == '志趣相投的朋友':
            # 朋友意向的6个维度计算
            if len(answers) >= 24:  # 确保有足够的答案
                # 维度一：兴趣共鸣 (I)
                I1_raw = len(answers[0].split('|')) if answers[0] else 0
                I1_raw = min(I1_raw, 5)  # 最多选5项
                I1 = 1 + (I1_raw / 5) * 4
                I2 = float(answers[1]) if answers[1] else 0
                I3 = float(answers[2]) if answers[2] else 0
                I4 = float(answers[3]) if answers[3] else 0
                I = (I1 + I2 + I3 + I4) / 4
                scores['I'] = round(I, 1)
                
                # 维度二：价值观契合 (V)
                V1_raw = len(answers[4].split('|')) if answers[4] else 0
                V1_raw = min(V1_raw, 5)  # 最多选5项
                V1 = 1 + (V1_raw / 5) * 4
                V2 = float(answers[5]) if answers[5] else 0
                V3 = float(answers[6]) if answers[6] else 0
                V4 = float(answers[7]) if answers[7] else 0
                V = (V1 + V2 + V3 + V4) / 4
                scores['V'] = round(V, 1)
                
                # 维度三：性格相容 (P)
                P1_raw = len(answers[8].split('|')) if answers[8] else 0
                P1_raw = min(P1_raw, 3)  # 最多选3项
                P1 = 1 + (P1_raw / 3) * 4
                P2 = float(answers[9]) if answers[9] else 0
                P3 = float(answers[10]) if answers[10] else 0
                P4 = float(answers[11]) if answers[11] else 0
                P = (P1 + P2 + P3 + P4) / 4
                scores['P'] = round(P, 1)
                
                # 维度四：生活节奏 (L)
                L1 = float(answers[12]) if answers[12] else 0
                L2_raw = len(answers[13].split('|')) if answers[13] else 0
                L2_raw = min(L2_raw, 5)  # 最多选5项
                L2 = 1 + (L2_raw / 5) * 4
                L3 = float(answers[14]) if answers[14] else 0
                L4 = float(answers[15]) if answers[15] else 0
                L = (L1 + L2 + L3 + L4) / 4
                scores['L'] = round(L, 1)
                
                # 维度五：情感支持 (E)
                E1_raw = len(answers[16].split('|')) if answers[16] else 0
                E1_raw = min(E1_raw, 5)  # 最多选5项
                E1 = 1 + (E1_raw / 5) * 4
                E2 = float(answers[17]) if answers[17] else 0
                E3 = float(answers[18]) if answers[18] else 0
                E4 = float(answers[19]) if answers[19] else 0
                E = (E1 + E2 + E3 + E4) / 4
                scores['E'] = round(E, 1)
                
                # 维度六：成长动力 (G)
                G1_raw = len(answers[20].split('|')) if answers[20] else 0
                G1_raw = min(G1_raw, 5)  # 最多选5项
                G1 = 1 + (G1_raw / 5) * 4
                G2 = float(answers[21]) if answers[21] else 0
                G3 = float(answers[22]) if answers[22] else 0
                G4 = float(answers[23]) if answers[23] else 0
                G = (G1 + G2 + G3 + G4) / 4
                scores['G'] = round(G, 1)
                
                # 匹配意向分数是各维度得分，不计算总分
                # 专注于各维度得分，不计算overall
    
    except Exception as e:
        print(f"计算意向分数时出错: {e}")
        # 返回空的维度分数字典
        scores = {}
    
    # 匹配意向分数是各维度得分，不需要overall字段
    
    return scores

# 提交匹配意向
@app.route('/api/matching-intent', methods=['POST'])
def submit_intent():
    # 验证请求数据
    if not request.json:
        return jsonify({'status': 'error', 'message': '请求数据格式错误'})
    
    data = request.json
    
    # 验证必需字段
    required_fields = ['user_id', 'intent_type', 'answers']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'status': 'error', 'message': f'缺少必需字段: {field}'})
    
    # 验证意向类型
    valid_intent_types = ['伴侣', '志趣相投的朋友']
    if data['intent_type'] not in valid_intent_types:
        return jsonify({'status': 'error', 'message': '无效的意向类型'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 验证用户是否存在
        cursor.execute('SELECT id FROM users WHERE id = ?', (data.get('user_id'),))
        user_exists = cursor.fetchone()
        if not user_exists:
            conn.close()
            return jsonify({'status': 'error', 'message': '用户不存在'})
        
        # 计算意向分数
        intent_scores = calculate_intent_scores(data.get('intent_type'), data.get('answers'))
        
        # 更新用户表的profile_scores字段，将意向分数作为个人属性存储
        cursor.execute('SELECT profile_scores FROM users WHERE id = ?', (data.get('user_id'),))
        user = cursor.fetchone()
        
        if user:
            # 解析现有的profile_scores
            existing_scores = {}
            if user['profile_scores']:
                try:
                    existing_scores = json.loads(user['profile_scores'])
                except:
                    existing_scores = {}
            
            # 添加意向分数到profile_scores，作为个人特有属性
            intent_key = f"intent_{data.get('intent_type')}"
            existing_scores[intent_key] = intent_scores
            
            # 根据意向类型更新对应的答案字段
            if data.get('intent_type') == '伴侣':
                # 更新伴侣意向答案
                cursor.execute('''
                UPDATE users SET profile_scores = ?, partner_intent_answers = ?
                WHERE id = ?
                ''', (json.dumps(existing_scores), data.get('answers'), data.get('user_id')))
            else:
                # 更新朋友意向答案
                cursor.execute('''
                UPDATE users SET profile_scores = ?, friend_intent_answers = ?
                WHERE id = ?
                ''', (json.dumps(existing_scores), data.get('answers'), data.get('user_id')))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'message': '匹配意向保存成功',
            'scores': intent_scores
        })
    
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        print(f"数据库操作错误: {e}")
        return jsonify({'status': 'error', 'message': '数据库操作失败，请稍后重试'})
    
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"保存匹配意向时出错: {e}")
        return jsonify({'status': 'error', 'message': f'保存失败: {str(e)}'})

# 获取用户的所有匹配意向
@app.route('/api/matching-intent/<user_id>', methods=['GET'])
def get_user_intents(user_id):
    """获取用户的所有匹配意向"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 从users表获取用户的匹配意向答案
    cursor.execute('SELECT partner_intent_answers, friend_intent_answers FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    
    # 转换为字典列表
    intent_list = []
    
    # 检查是否有伴侣意向答案
    if user and user['partner_intent_answers']:
        intent_list.append({
            'id': f"intent_partner_{user_id}",
            'user_id': user_id,
            'intent_type': '伴侣',
            'answers': user['partner_intent_answers']
        })
    
    # 检查是否有朋友意向答案
    if user and user['friend_intent_answers']:
        intent_list.append({
            'id': f"intent_friend_{user_id}",
            'user_id': user_id,
            'intent_type': '志趣相投的朋友',
            'answers': user['friend_intent_answers']
        })
    
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
    cursor.execute('SELECT id, username, name, age, gender, location, avatar FROM users')
    users = cursor.fetchall()
    
    conn.close()
    
    # 转换为字典列表
    user_list = []
    for user in users:
        user_dict = dict(user)
        # 如果用户有头像，生成完整的头像URL
        if user_dict.get('avatar'):
            user_dict['avatar'] = f'http://localhost:5000/avatars/{user_dict["avatar"]}'
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
@app.route('/api/friend-request/send', methods=['POST'])
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
        INSERT INTO received_friend_requests (from_user_id, to_user_id, from_user_name, message)
        VALUES (?, ?, ?, ?)
    ''', (from_user_id, to_user_id, from_user_name, message))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

# 获取用户的意向申请
@app.route('/api/friend-requests/<user_id>', methods=['GET'])
def get_intent_requests(user_id):
    """获取用户的意向申请"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM received_friend_requests
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
@app.route('/api/friend-request/accept', methods=['POST'])
def accept_intent_request():
    """接受意向申请"""
    data = request.json
    request_id = data.get('request_id')
    
    if not request_id:
        return jsonify({'status': 'error', 'message': '缺少申请ID'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取意向申请的详细信息
    cursor.execute('SELECT * FROM received_friend_requests WHERE id = ?', (request_id,))
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
    cursor.execute('UPDATE received_friend_requests SET status = ? WHERE id = ?', ('accepted', request_id))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

# 拒绝意向申请
@app.route('/api/friend-request/reject', methods=['POST'])
def reject_intent_request():
    """拒绝意向申请"""
    data = request.json
    request_id = data.get('request_id')
    
    if not request_id:
        return jsonify({'status': 'error', 'message': '缺少申请ID'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE received_friend_requests SET status = ? WHERE id = ?', ('rejected', request_id))
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
    cursor.execute('SELECT COUNT(*) FROM received_friend_requests WHERE to_user_id = ? AND status = ?', (user_id, 'pending'))
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