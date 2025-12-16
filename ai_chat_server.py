from http.server import BaseHTTPRequestHandler, HTTPServer
from openai import OpenAI
import urllib.parse
import json
import uuid
from datetime import datetime
import os
import random

# 初始化OpenAI客户端
client = OpenAI(
    api_key="sk-fzL1g6l3ouBhGi0Lqq1HScXZFlSqJrq6TOpFjJBBVsqCOSYB",
    base_url="https://api.chatanywhere.tech/v1"
)

# 内存存储数据结构
sessions = {}  # 存储对话历史
projects = {}   # 存储代码项目
learning_progress = {}  # 存储学习进度

def gpt_35_api_stream(messages: list, temperature=0.7):
    """流式调用GPT-3.5"""
    try:
        stream = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=messages,
            stream=True,
            temperature=temperature
        )
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
        return full_response
    except Exception as e:
        return f"抱歉，调用AI服务时出现错误：{str(e)}"

def generate_preview_material(level, topic):
    """生成分层预习材料"""
    level_descriptions = {
        "easy": "基础版，适合需要巩固基础知识的同学",
        "medium": "标准版，适合大多数同学的学习节奏", 
        "hard": "进阶版，适合学有余力的同学拓展学习"
    }
    
    prompt = f"""
    请为高中信息技术课程生成关于"{topic}"的预习材料。
    难度级别：{level_descriptions[level]}
    
    请按照以下结构组织内容：
    1. 核心概念介绍
    2. 关键知识点解析
    3. 简单易懂的示例
    4. 预习思考题（3-5个问题）
    
    请确保内容适合{level}水平的学生，语言通俗易懂。
    """
    
    messages = [
        {"role": "system", "content": "你是一位经验丰富的高中信息技术教师，擅长制作分层预习材料。"},
        {"role": "user", "content": prompt}
    ]
    
    return gpt_35_api_stream(messages)

def debug_code(code, error_message=""):
    """代码调试功能"""
    prompt = f"""
    请帮我调试以下Python代码：
    {code}
    """
    
    if error_message:
        prompt += f"\n错误信息：{error_message}"
    
    prompt += """
    请：
    1. 分析代码中的问题
    2. 提供修正后的代码
    3. 解释修正的原因
    """
    
    #1: "指出错误类型和位置，但不直接给出答案",
    #2: "提供类似问题的解决思路", 
    #3: "给出部分修正代码，保留关键思考空间"
    
    messages = [
        {"role": "system", "content": "你是一位专业的编程导师，擅长调试Python代码。"},
        {"role": "user", "content": prompt}
    ]
    
    return gpt_35_api_stream(messages)

def explain_code(code):
    """代码解释功能"""
    prompt = f"""
    请详细解释以下Python代码：
    {code}
    
    请从以下方面进行解释：
    1. 代码的功能和作用
    2. 关键语句的含义
    3. 可能的改进建议
    4. 相关的编程概念
    """
    
    messages = [
        {"role": "system", "content": "你是一位耐心的编程教师，擅长用简单语言解释复杂代码。"},
        {"role": "user", "content": prompt}
    ]
    
    return gpt_35_api_stream(messages)

def generate_personalized_exercise(topic, student_level):
    """生成个性化练习题"""
    difficulty_map = {
        "easy": "简单",
        "medium": "中等", 
        "hard": "困难"
    }
    
    prompt = f"""
    为高中信息技术课程生成关于"{topic}"的练习题。
    难度：{difficulty_map[student_level]}
    学生水平：{student_level}
    
    请提供：
    1. 题目描述
    2. 解题思路提示
    3. 参考答案
    4. 相关的知识点回顾
    """
    
    messages = [
        {"role": "system", "content": "你是一位优秀的试题编写专家，擅长设计分层练习题。"},
        {"role": "user", "content": prompt}
    ]
    
    return gpt_35_api_stream(messages)

def analyze_learning_progress(conversation_history):
    """分析学习进度并提供建议"""
    prompt = f"""
    基于以下学习对话历史，分析学生的学习情况并提供个性化建议：
    {conversation_history}
    
    请从以下方面进行分析：
    1. 知识掌握情况
    2. 学习中的难点
    3. 下一步学习建议
    4. 推荐的练习重点
    """
    
    messages = [
        {"role": "system", "content": "你是一位专业的学习分析师，擅长通过对话分析学习情况。"},
        {"role": "user", "content": prompt}
    ]
    
    return gpt_35_api_stream(messages)
    
def generate_homework(difficulty, topic="Python编程"):
    """生成个性化作业"""
    difficulty_map = {
        "easy": "基础",
        "medium": "中等", 
        "hard": "困难"
    }
    
    prompt = f"""
    为高中信息技术课程生成关于"{topic}"的个性化作业。
    难度：{difficulty_map[difficulty]}
    
    请按照以下结构生成作业：
    1. 作业目标
    2. 具体任务描述
    3. 要求与评分标准
    4. 拓展挑战（可选）
    
    请确保作业难度适合{difficulty}水平的学生，内容具有实践性和趣味性。
    """
    
    messages = [
        {"role": "system", "content": "你是一位经验丰富的教师，擅长设计分层个性化作业。"},
        {"role": "user", "content": prompt}
    ]
    
    return gpt_35_api_stream(messages)

def analyze_progress(session_id, conversation_history=None):
    """分析学习进度并返回结构化数据"""
    # 如果未提供对话历史，则从sessions中获取
    if conversation_history is None:
        session_data = sessions.get(session_id, {})
        conversation_history = []
        
        # 遍历所有phase，合并对话历史
        for phase, messages in session_data.items():
            conversation_history.extend(messages)
    
    # 计算对话历史中的消息数量
    history_count = len(conversation_history) if conversation_history else 0
    
    # 如果对话历史太少，返回数据不足的提示
    if history_count < 2:  # 至少需要一次完整的对话（用户提问+AI回答）
        return {
            "progress": 0,
            "suggestions": [],
            "strengths": [],
            "weaknesses": [],
            "data_insufficient": True,
            "message": "对话数据不足，无法进行有效分析。请先与AI助手进行更多互动。"
        }
    
    # 将对话历史转换为文本
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
    
    prompt = f"""
    基于以下学习对话历史，分析学生的学习情况并提供结构化数据：
    {history_text}
    
    请返回一个JSON格式的分析结果，包含以下字段：
    1. progress: 学习进度百分比（0-100之间的整数）
    2. suggestions: 建议复习的知识点列表（最多3个）
    3. strengths: 学生的优势知识点列表
    4. weaknesses: 学生的薄弱知识点列表
    5. data_insufficient: 布尔值，表示数据是否充足（固定为false）
    
    请确保返回的是纯JSON格式，不要有其他文本。
    """
    
    messages = [
        {"role": "system", "content": "你是一位专业的学习分析师，擅长通过对话分析学习情况。请只返回JSON格式的数据。"},
        {"role": "user", "content": prompt}
    ]
    
    try:
        analysis_text = gpt_35_api_stream(messages)
        
        # 尝试解析JSON
        import re
        json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            # 确保包含必要的字段
            if "data_insufficient" not in result:
                result["data_insufficient"] = False
            return result
        else:
            # 如果无法解析，返回默认值
            return {
                "progress": 75,
                "suggestions": ["循环结构", "函数定义"],
                "strengths": ["基础语法"],
                "weaknesses": ["复杂逻辑"],
                "data_insufficient": False
            }
    except:
        # 如果解析失败，返回默认值
        return {
            "progress": 75,
            "suggestions": ["循环结构", "函数定义"],
            "strengths": ["基础语法"],
            "weaknesses": ["复杂逻辑"],
            "data_insufficient": False
        }
        
# 定义请求处理器
class AIHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """设置CORS头部"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    # 处理GET请求
    def do_GET(self):
        self.send_response(200)
        self._set_cors_headers()
        
        if self.path == '/':
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            # 读取并返回HTML文件内容
            try:
                with open("ai_chat.html", "r", encoding="utf-8") as f:
                    html_content = f.read()
                self.wfile.write(html_content.encode("utf-8"))
            except FileNotFoundError:
                self.wfile.write("<h1>AI助学系统</h1><p>请确保ai_chat.html文件存在</p>".encode("utf-8"))
        
        elif self.path.startswith('/api/projects'):
            # 获取代码项目列表
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            # 从内存中获取项目列表
            project_list = []
            for project_id, project_data in projects.items():
                project_list.append({
                    "id": project_id,
                    "name": project_data.get("name", "未命名项目"),
                    "created_at": project_data.get("created_at", "")
                })
            
            # 按创建时间排序（最新的在前）
            project_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            response = {"projects": project_list[:10]}  # 只返回最新的10个项目
            
            self.wfile.write(json.dumps(response).encode("utf-8"))
        
        elif self.path.startswith('/api/project/'):
            # 获取特定项目
            project_id = self.path.split('/')[-1]
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            if project_id in projects:
                project_data = projects[project_id]
                response = {
                    "name": project_data.get("name", "未命名项目"),
                    "code": project_data.get("code", ""),
                    "output": project_data.get("output", "")
                }
            else:
                response = {"error": "项目不存在"}
            
            self.wfile.write(json.dumps(response).encode("utf-8"))
        
        else:
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("API端点不存在".encode('utf-8'))
    
    # 处理POST请求
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode("utf-8")
        
        # 根据Content-Type解析数据
        content_type = self.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            parsed_data = json.loads(post_data)
        else:
            parsed_data = urllib.parse.parse_qs(post_data)
            # 将列表值转换为单个值
            parsed_data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v 
                          for k, v in parsed_data.items()}
        
        # 设置响应头
        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        
        response = {"success": False, "message": "未知错误"}
        
        try:
            if self.path == '/api/chat':
                # 通用聊天接口
                user_message = parsed_data.get('message', '')
                session_id = parsed_data.get('session_id', 'default')
                phase = parsed_data.get('phase', 'general')
                
                # 获取或创建会话历史
                if session_id not in sessions:
                    sessions[session_id] = {}
                if phase not in sessions[session_id]:
                    sessions[session_id][phase] = []
                
                # 添加用户消息
                sessions[session_id][phase].append({'role': 'user', 'content': user_message})
                
                # 调用GPT API
                ai_response = gpt_35_api_stream(sessions[session_id][phase])
                
                # 添加AI回复
                sessions[session_id][phase].append({'role': 'assistant', 'content': ai_response})
                
                response = {"success": True, "message": ai_response, "session_id": session_id}
            
            elif self.path == '/api/preview':
                # 生成预习材料
                level = parsed_data.get('level', 'standard')
                topic = parsed_data.get('topic', 'Python编程基础')
                
                material = generate_preview_material(level, topic)
                response = {"success": True, "material": material, "level": level}
            
            elif self.path == '/api/debug':
                # 代码调试
                code = parsed_data.get('code', '')
                error = parsed_data.get('error', '')
                
                debug_result = debug_code(code, error)
                response = {"success": True, "result": debug_result}
            
            elif self.path == '/api/explain':
                # 代码解释
                code = parsed_data.get('code', '')
                
                explanation = explain_code(code)
                response = {"success": True, "explanation": explanation}
            
            elif self.path == '/api/exercise':
                # 生成个性化练习
                topic = parsed_data.get('topic', '编程基础')
                level = parsed_data.get('level', 'easy')
                
                exercise = generate_personalized_exercise(topic, level)
                response = {"success": True, "exercise": exercise}
            
            elif self.path == '/api/analyze':
                # 分析学习进度
                session_id = parsed_data.get('session_id', 'default')
                
                # 获取session_id下的所有对话历史（不按phase筛选）
                session_data = sessions.get(session_id, {})
                conversation_history = []
                
                # 遍历所有phase，合并对话历史
                for phase, messages in session_data.items():
                    conversation_history.extend(messages)
                
                if conversation_history:
                    # 将对话历史转换为文本
                    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
                    analysis = analyze_learning_progress(history_text)
                    response = {"success": True, "analysis": analysis}
                else:
                    response = {"success": False, "message": "没有找到对话历史"}
            
            elif self.path == '/api/generate-homework':
                # 生成个性化作业
                difficulty = parsed_data.get('difficulty', 'medium')
                session_id = parsed_data.get('session_id', 'default')
                
                homework = generate_homework(difficulty)
                response = {"success": True, "homework": homework}
            
            elif self.path == '/api/analyze-progress':
                # 分析学习进度并返回结构化数据
                session_id = parsed_data.get('session_id', 'default')
                
                # 获取session_id下的所有对话历史
                session_data = sessions.get(session_id, {})
                conversation_history = []
                
                # 遍历所有phase，合并对话历史
                for phase, messages in session_data.items():
                    conversation_history.extend(messages)
                
                progress_data = analyze_progress(session_id, conversation_history)
                # 确保所有字段都有值，处理空值情况
                progress_value = progress_data.get('progress', 0)  # 默认为0
                suggestions = progress_data.get('suggestions', [])  # 默认为空数组
                strengths = progress_data.get('strengths', [])  # 默认为空数组
                weaknesses = progress_data.get('weaknesses', [])  # 默认为空数组
                data_insufficient = progress_data.get('data_insufficient', False)  # 默认为False
                message = progress_data.get('message', '')  # 默认为空字符串
                
                # 如果数据不足，设置success为False并包含提示消息
                if progress_data.get('data_insufficient', False):
                    response = {
                        "success": False, 
                        "message": message or '数据不足，无法进行有效分析',
                        "data_insufficient": True
                    }
                else:
                    response = {
                        "success": True, 
                        "progress": progress_value,
                        "suggestions": suggestions,
                        "strengths": strengths,
                        "weaknesses": weaknesses,
                        "data_insufficient": data_insufficient
                    }
                    if message:
                        response["message"] = message
                
            elif self.path == '/api/save-project':
                # 保存代码项目
                project_id = parsed_data.get('id', str(uuid.uuid4()))
                name = parsed_data.get('name', f'项目_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                code = parsed_data.get('code', '')
                output = parsed_data.get('output', '')
                
                # 保存到内存
                projects[project_id] = {
                    "name": name,
                    "code": code,
                    "output": output,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                response = {"success": True, "project_id": project_id}
            
            else:
                response = {"success": False, "message": "不支持的API端点"}
        
        except Exception as e:
            response = {"success": False, "message": f"服务器错误: {str(e)}"}
        
        # 返回JSON响应
        self.wfile.write(json.dumps(response).encode("utf-8"))

# 启动服务器
def run_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, AIHandler)
    print("="*60)
    print("AI助学系统服务器已启动（无数据库版本）")
    print("访问 http://localhost:8000 开始使用")
    print("注意：数据存储在内存中，重启服务器将丢失所有数据")
    print("支持的API端点:")
    print("  GET  /                    - 前端页面")
    print("  POST /api/chat            - 通用聊天")
    print("  POST /api/preview         - 生成预习材料")
    print("  POST /api/debug           - 代码调试")
    print("  POST /api/explain         - 代码解释")
    print("  POST /api/exercise        - 生成个性化练习")
    print("  POST /api/analyze         - 学习进度分析")
    print("  POST /api/generate-homework - 生成课后个性化作业")
    print("  POST /api/analyze-progress - 分析课后学习进度（结构化数据）")
    print("  POST /api/save-project    - 保存代码项目")
    print("  GET  /api/projects        - 获取项目列表")
    print("  GET  /api/project/{id}    - 获取特定项目")
    print("="*60)
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()