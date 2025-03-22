import os
import logging
import math
import requests
import re
from flask import Flask, request, render_template_string, jsonify
import random
import jieba

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TextPrimeFinder')

app = Flask(__name__)

# PrimesDB 相關常量和函數
PRIMESDB_URL = "https://github.com/pekesoft/PrimesDB/raw/main/PrimesDB/0000.pdb"
PRIMESDB_CACHE_FILE = "primesdb_cache.bin"
primesdb_data = None

def download_primesdb():
    """下載 PrimesDB 數據文件"""
    global primesdb_data
    try:
        # 首先檢查是否有本地緩存
        if os.path.exists(PRIMESDB_CACHE_FILE):
            logger.info(f"從本地緩存加載 PrimesDB: {PRIMESDB_CACHE_FILE}")
            with open(PRIMESDB_CACHE_FILE, 'rb') as f:
                primesdb_data = f.read()
            return True
        
        # 如果沒有本地緩存，從 GitHub 下載
        logger.info(f"從 GitHub 下載 PrimesDB: {PRIMESDB_URL}")
        response = requests.get(PRIMESDB_URL)
        if response.status_code == 200:
            primesdb_data = response.content
            # 保存到本地緩存
            with open(PRIMESDB_CACHE_FILE, 'wb') as f:
                f.write(primesdb_data)
            logger.info(f"PrimesDB 下載成功，大小: {len(primesdb_data)} 字節")
            return True
        else:
            logger.error(f"下載 PrimesDB 失敗: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"下載 PrimesDB 時出錯: {e}")
        return False

def is_prime_primesdb(number):
    """使用 PrimesDB 檢查一個數字是否為質數"""
    global primesdb_data
    
    # 如果數據未加載，嘗試加載
    if primesdb_data is None:
        if not download_primesdb():
            # 如果無法加載 PrimesDB，回退到傳統方法
            return is_prime(number)
    
    # 使用 PrimesDB 算法檢查質數
    # 首先檢查基本情況
    if number < 2:
        return False
    if number == 2 or number == 3 or number == 5 or number == 7:
        return True
    if number % 2 == 0 or number % 3 == 0 or number % 5 == 0:
        return False
    
    # 只檢查末尾為 1, 3, 7, 9 的數字
    last_digit = number % 10
    if last_digit not in [1, 3, 7, 9]:
        return False
    
    # 計算 PrimesDB 中的位置
    decade = number // 10
    address = int(decade / 2 + 0.5) - 1
    
    # 檢查地址是否在數據範圍內
    if address < 0 or address >= len(primesdb_data):
        # 如果超出範圍，回退到傳統方法
        return is_prime(number)
    
    # 計算位偏移
    bit_positions = {1: 0, 3: 1, 7: 2, 9: 3}
    bit_pos = bit_positions[last_digit]
    
    # 如果十位數是偶數，使用高位元組
    if decade % 2 == 0:
        bit_pos += 4
    
    # 獲取字節並檢查相應的位
    byte_value = primesdb_data[address]
    is_prime_value = (byte_value >> bit_pos) & 1
    
    return is_prime_value == 1

def is_prime(n):
    """傳統方法檢查質數"""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def find_primes_near(number, count, direction):
    """查找指定數字附近的質數"""
    global primesdb_data
    
    # 如果數據未加載，嘗試加載
    if primesdb_data is None:
        if not download_primesdb():
            # 如果無法加載 PrimesDB，回退到傳統方法
            return find_primes_near_traditional(number, count, direction)
    
    # 如果數字超過 PrimesDB 的範圍 (約 1,342,177,280)，使用傳統方法
    if number > 1000000000:  # 設置一個安全的閾值
        return find_primes_near_traditional(number, count, direction)
    
    result = []
    current = number
    
    # 根據方向調整步進
    step = 1 if direction == 'larger' else -1
    
    # 如果是向下查找，先減 1
    if direction == 'smaller':
        current -= 1
    # 如果是向上查找，先加 1
    else:
        current += 1
    
    # 查找指定數量的質數
    while len(result) < count and current > 1 and current < 10**10:  # 設置一個上限，避免無限循環
        if is_prime_primesdb(current):
            result.append(current)
        current += step
    
    return result

def find_primes_near_traditional(number, count, direction):
    """使用傳統方法查找指定數字附近的質數"""
    result = []
    current = number
    
    # 根據方向調整步進
    step = 1 if direction == 'larger' else -1
    
    # 如果是向下查找，先減 1
    if direction == 'smaller':
        current -= 1
    # 如果是向上查找，先加 1
    else:
        current += 1
    
    # 查找指定數量的質數
    while len(result) < count and current > 1:
        if is_prime(current):
            result.append(current)
        current += step
    
    return result

def find_closest_primes(number, count=5):
    """找出離指定數字最近的質數"""
    try:
        logger.info(f"查詢最接近 {number} 的質數，數量: {count}")
        
        # 使用 PrimesDB 查找較大和較小的質數
        larger_primes = find_primes_near(number, count, 'larger')
        smaller_primes = find_primes_near(number, count, 'smaller')
        
        logger.info(f"查詢結果: 較大質數 {len(larger_primes)} 個, 較小質數 {len(smaller_primes)} 個")
        
        # 合併結果並計算距離
        result = []
        
        # 處理較大的質數
        for prime in larger_primes:
            distance = prime - number
            result.append((prime, distance))
        
        # 處理較小的質數
        for prime in smaller_primes:
            distance = number - prime
            result.append((prime, distance))
        
        # 按距離排序
        result.sort(key=lambda x: x[1])
        
        # 限制結果數量
        result = result[:count]
        
        # 將結果轉換為字典
        results = []
        for prime, distance in result:
            results.append({
                'prime': prime,
                'distance': distance
            })
        
        logger.info(f"最終結果: {results}")
        
        return results
    except Exception as e:
        logger.error(f"查詢質數時出錯: {e}")
        return []

def text_to_base36(text):
    """將文字轉換為36進位數字"""
    if not text:
        return 0
    
    # 1. 檢查是否為純數字
    if text.isdigit():
        return int(text)
    
    # 2. 檢查是否只包含英文字母和數字
    if all(c.isalnum() and ord(c) < 128 for c in text):
        # 含有英文字母，視為36進位
        result = 0
        for char in text.upper():
            if '0' <= char <= '9':
                value = int(char)
            elif 'A' <= char <= 'Z':
                value = ord(char) - ord('A') + 10
            else:
                # 忽略不在36進位範圍內的字符
                continue
            result = result * 36 + value
        return result
    
    # 3. 包含其他Unicode字符，使用簡化的哈希方法
    # 使用簡單的哈希算法，避免超大數字
    result = 0
    for char in text:
        result = (result * 31 + ord(char)) % (10**15)
    
    return result

def base36_to_text(number, original_text):
    """將36進位數字轉換回文字"""
    if not original_text:
        return str(number)
    
    # 1. 檢查原始文字是否為純數字
    if original_text.isdigit():
        return str(number)
    
    # 2. 檢查是否只包含英文字母和數字
    if all(c.isalnum() and ord(c) < 128 for c in original_text):
        # 含有英文字母，需要轉換回36進位表示
        result = ""
        temp = number
        
        # 獲取原始文字的長度（忽略非36進位字符）
        valid_chars = 0
        for char in original_text:
            if ('0' <= char <= '9') or ('A' <= char <= 'Z') or ('a' <= char <= 'z'):
                valid_chars += 1
        
        # 如果沒有有效字符，直接返回數字
        if valid_chars == 0:
            return str(number)
        
        # 轉換為36進位
        while temp > 0 or len(result) < valid_chars:
            digit = temp % 36
            if digit < 10:
                result = str(digit) + result
            else:
                result = chr(digit - 10 + ord('A')) + result
            temp //= 36
            
            if len(result) >= valid_chars:
                break
        
        # 如果結果長度不足，前面補0
        while len(result) < valid_chars:
            result = '0' + result
        
        return result
    
    # 3. 包含Unicode字符，生成有趣的替換
    # 對於Unicode文字，生成一個相似但不同的Unicode字符
    result = ""
    for char in original_text:
        # 獲取字符的Unicode碼點
        code_point = ord(char)
        
        # 根據數字生成一個小偏移，使字符略有變化但仍保持在同一Unicode區塊
        # 對於中文字符，保持在中文區塊內
        if 0x4E00 <= code_point <= 0x9FFF:  # 中文字符範圍
            # 計算一個偏移，保持在中文範圍內
            offset = (number % 100) - 50  # -50 到 49 的偏移
            new_code = code_point + offset
            # 確保仍在中文範圍內
            if new_code < 0x4E00:
                new_code = 0x4E00 + (new_code % 100)
            elif new_code > 0x9FFF:
                new_code = 0x9FFF - (new_code % 100)
        else:
            # 對於其他Unicode字符，使用較小的偏移
            offset = (number % 20) - 10  # -10 到 9 的偏移
            new_code = code_point + offset
        
        # 將新的碼點轉換為字符
        try:
            result += chr(new_code)
        except:
            # 如果轉換失敗，使用原始字符
            result += char
    
    return result

def find_prime_replacements(words, count=5):
    """為每個單詞找到最接近的質數替換"""
    result = []
    
    for word in words:
        original = word['original']
        numeric = word['numeric']
        is_prime = word['is_prime']
        
        # 如果數字本身是質數，不需要替換
        if is_prime:
            result.append({
                'original': original,
                'numeric': numeric,
                'is_prime': True,
                'replacements': []
            })
            continue
        
        # 查找最接近的質數
        closest_primes = find_closest_primes(numeric, count)
        
        # 將質數轉換回文字
        replacements = []
        for prime_info in closest_primes:
            prime = prime_info['prime']
            distance = prime_info['distance']
            direction = '+' if prime > numeric else '-'
            
            # 將質數轉換為文字
            text = base36_to_text(prime, original)
            
            replacements.append({
                'prime': prime,
                'text': text,
                'distance': distance,
                'direction': direction
            })
        
        result.append({
            'original': original,
            'numeric': numeric,
            'is_prime': False,
            'replacements': replacements
        })
    
    return result

def parse_text(text, chinese_mode="auto"):
    """
    解析文本，將其分割為單詞，並轉換為數字
    
    chinese_mode 參數控制中文處理方式:
    - "auto": 自動使用jieba進行詞彙分割
    - "char": 將每個中文字符視為獨立單元
    - "space": 使用空格作為分隔符，由用戶手動分詞
    """
    # 檢查文本是否包含中文字符
    has_chinese = any(0x4E00 <= ord(c) <= 0x9FFF for c in text)
    
    if has_chinese:
        if chinese_mode == "char":
            # 按字符處理中文
            chinese_chars = [c for c in text if 0x4E00 <= ord(c) <= 0x9FFF]
            
            # 提取非中文部分（按空格分割）
            non_chinese = []
            for part in text.split():
                if not any(0x4E00 <= ord(c) <= 0x9FFF for c in part):
                    non_chinese.append(part)
            
            # 合併所有單元
            words = chinese_chars + non_chinese
        
        elif chinese_mode == "space":
            # 使用空格作為分隔符，由用戶手動分詞
            words = [word for word in text.split() if word]
        
        else:  # "auto" 模式，使用jieba分詞
            # 使用jieba進行中文分詞
            seg_list = jieba.cut(text, cut_all=False)
            words = [word for word in seg_list if word.strip()]
    else:
        # 對於非中文文本，按空格分割
        words = [word for word in text.split() if word]
    
    # 轉換每個單詞為數字
    result = []
    for word in words:
        num_value = text_to_base36(word)
        result.append({
            'original': word,
            'numeric': num_value,
            'is_prime': is_prime_primesdb(num_value)
        })
    
    return result

def generate_random_combinations(words, max_combinations=5):
    """生成隨機的質數替換組合"""
    if not words:
        return []
    
    combinations = []
    
    # 計算可能的組合數量
    max_possible = min(max_combinations, 10)  # 限制最大組合數
    
    for _ in range(max_possible):
        combination = []
        for word in words:
            if word['is_prime']:
                # 如果原詞已經是質數，保留原詞
                combination.append({
                    'original': word['original'],
                    'replacement': word['original'],
                    'numeric': word['numeric'],
                    'is_original': True
                })
            elif word['replacements']:
                # 隨機選擇一個替換
                replacement = random.choice(word['replacements'])
                combination.append({
                    'original': word['original'],
                    'replacement': replacement['text'],
                    'numeric': replacement['prime'],
                    'distance': replacement['distance'],
                    'direction': replacement['direction'],
                    'is_original': False
                })
            else:
                # 沒有替換選項，保留原詞
                combination.append({
                    'original': word['original'],
                    'replacement': word['original'],
                    'numeric': word['numeric'],
                    'is_original': True
                })
        
        combinations.append(combination)
    
    return combinations

@app.route('/')
def index():
    return render_template_string(get_index_template())

@app.route('/search', methods=['POST'])
def search():
    try:
        text = request.form.get('text', '')
        chinese_mode = request.form.get('chinese_mode', 'auto')
        count = int(request.form.get('count', '10'))
        
        # 限制結果數量在 1-512 之間
        count = max(1, min(512, count))
        
        if not text.strip():
            return jsonify({'error': '請輸入文字'}), 400
        
        # 解析文本
        parsed_words = parse_text(text, chinese_mode)
        
        # 查找質數替換
        prime_replacements = find_prime_replacements(parsed_words, count)
        
        # 生成隨機組合
        combinations = generate_random_combinations(prime_replacements, 5)
        
        # 準備數值表示
        numeric_representation = []
        for word in parsed_words:
            numeric_representation.append(str(word['numeric']))
        
        # 準備質數替換表示
        prime_representation = []
        for word in prime_replacements:
            if word['is_prime']:
                prime_representation.append(f"{word['original']}")
            elif word['replacements']:
                replacement = word['replacements'][0]
                prime_representation.append(f"{replacement['text']}{replacement['direction']}{replacement['distance']}")
            else:
                prime_representation.append(word['original'])
        
        return jsonify({
            'original_text': text,
            'parsed_words': parsed_words,
            'prime_replacements': prime_replacements,
            'numeric_representation': ' '.join(numeric_representation),
            'prime_representation': ' '.join(prime_representation),
            'combinations': combinations,
            'count': count
        })
    
    except Exception as e:
        logger.error(f"處理請求時出錯: {e}")
        return jsonify({'error': f'處理請求時出錯: {str(e)}'}), 500

def get_index_template():
    """獲取首頁模板"""
    return '''
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>文字與質數的距離</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .container {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            .form-container {
                display: flex;
                align-items: flex-end;
                gap: 15px;
                margin-bottom: 20px;
            }
            .form-group {
                flex: 1;
            }
            .count-group {
                width: 100px;
                flex: none;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="text"], input[type="number"], textarea {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
                box-sizing: border-box;
            }
            textarea {
                height: 100px;
                resize: vertical;
            }
            button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s;
                height: 38px;
            }
            button:hover {
                background-color: #2980b9;
            }
            #results {
                margin-top: 30px;
                display: none;
            }
            .result-header {
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            .result-section {
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 4px;
            }
            .word-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            .word-item:last-child {
                border-bottom: none;
            }
            .word-info {
                margin-bottom: 10px;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
                color: #333;
            }
            .word-info:nth-child(odd) {
                background-color: #f5f5f5;
            }
            .word-info:nth-child(even) {
                background-color: #e9e9e9;
            }
            .word-info.is-prime {
                border-left: 4px solid #4caf50;
            }
            .word-info.not-prime {
                border-left: 4px solid #f44336;
            }
            .prime-list {
                margin-top: 10px;
            }
            .prime-item {
                display: flex;
                justify-content: space-between;
                padding: 5px 0;
                border-bottom: 1px dashed #eee;
            }
            .prime-item:last-child {
                border-bottom: none;
            }
            .combination {
                margin-bottom: 15px;
                padding: 10px;
                background-color: #e3f2fd;
                border-radius: 4px;
                border: 1px solid #bbdefb;
            }
            .loading {
                text-align: center;
                margin: 20px 0;
                display: none;
            }
            .error {
                color: #721c24;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                padding: 10px;
                border-radius: 4px;
                margin-top: 20px;
                display: none;
            }
            .celebration {
                text-align: center;
                font-size: 24px;
                margin: 20px 0;
                animation: celebrate 1s infinite;
                display: none;
            }
            @keyframes celebrate {
                0% { transform: scale(1); }
                50% { transform: scale(1.2); }
                100% { transform: scale(1); }
            }
            .footer {
                text-align: center;
                margin-top: 20px;
                font-size: 14px;
                color: #777;
                padding-top: 10px;
                border-top: 1px solid #eee;
            }
            .footer a {
                color: #3498db;
                text-decoration: none;
            }
            .footer a:hover {
                text-decoration: underline;
            }
            .highlight {
                font-weight: bold;
                color: #e74c3c;
            }
            .numeric-display {
                font-family: monospace;
                white-space: pre-wrap;
                word-break: break-all;
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
            }
            .prime-text {
                font-weight: bold;
                color: #2980b9;
            }
            .distance-indicator {
                font-size: 0.85em;
                color: #e74c3c;
                margin-left: 2px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>文字與質數的距離</h1>
            
            <div class="form-container">
                <div class="form-group">
                    <label for="text_input">請輸入文字：</label>
                    <textarea id="text_input" placeholder="例如：Hello World 或 I am a 60 years old man."></textarea>
                </div>
                <div class="form-group">
                    <label for="chinese_mode">中文處理模式：</label>
                    <select id="chinese_mode">
                        <option value="auto">自動（使用jieba）</option>
                        <option value="char">按字符處理</option>
                        <option value="space">按空格分隔</option>
                    </select>
                </div>
                <div class="count-group">
                    <label for="result_count">結果數量：</label>
                    <input type="number" id="result_count" value="10" min="1" max="512">
                </div>
                
                <button id="search_btn">查詢</button>
            </div>
            
            <div class="loading" id="loading">
                <p>正在查詢中，請稍候...</p>
            </div>
            
            <div class="error" id="error"></div>
            
            <div id="results">
                <div class="result-header">
                    <h2>查詢結果</h2>
                    <p id="text_display"></p>
                </div>
                
                <div class="result-section">
                    <h3>數值表示</h3>
                    <div id="numeric_display" class="numeric-display"></div>
                </div>
                
                <div class="result-section">
                    <h3>質數替換</h3>
                    <div id="prime_display" class="combination"></div>
                </div>
                
                <div class="result-section">
                    <h3>單詞分析</h3>
                    <div id="word_analysis"></div>
                </div>
                
                <div class="result-section">
                    <h3>隨機質數組合</h3>
                    <div id="combinations"></div>
                </div>
            </div>
            
            <div class="footer">
                <p> 2025 質人精神：文字與質數的距離 | 基於<a href="https://github.com/pekesoft/PrimesDB" target="_blank">PrimesDB</a>高效質數資料庫的應用</p>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const searchBtn = document.getElementById('search_btn');
                const textInput = document.getElementById('text_input');
                const chineseModeSelect = document.getElementById('chinese_mode');
                const resultCountInput = document.getElementById('result_count');
                const resultsDiv = document.getElementById('results');
                const textDisplay = document.getElementById('text_display');
                const numericDisplay = document.getElementById('numeric_display');
                const primeDisplay = document.getElementById('prime_display');
                const wordAnalysis = document.getElementById('word_analysis');
                const combinations = document.getElementById('combinations');
                const loading = document.getElementById('loading');
                const errorDiv = document.getElementById('error');
                
                // 添加回車鍵搜索功能
                textInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        searchBtn.click();
                    }
                });
                
                resultCountInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        searchBtn.click();
                    }
                });
                
                searchBtn.addEventListener('click', function() {
                    const text = textInput.value.trim();
                    const chineseMode = chineseModeSelect.value;
                    const count = parseInt(resultCountInput.value) || 10;
                    
                    // 限制結果數量在 1-512 之間
                    const limitedCount = Math.max(1, Math.min(512, count));
                    
                    if (!text) {
                        showError('請輸入文字');
                        return;
                    }
                    
                    // 重置顯示
                    resultsDiv.style.display = 'none';
                    errorDiv.style.display = 'none';
                    loading.style.display = 'block';
                    
                    // 創建 FormData
                    const formData = new FormData();
                    formData.append('text', text);
                    formData.append('chinese_mode', chineseMode);
                    formData.append('count', limitedCount);
                    
                    // 發送請求
                    fetch('/search', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(data => {
                                throw new Error(data.error || '請求失敗');
                            });
                        }
                        return response.json();
                    })
                    .then(data => {
                        loading.style.display = 'none';
                        displayResults(data);
                    })
                    .catch(error => {
                        loading.style.display = 'none';
                        showError(error.message);
                    });
                });
                
                function displayResults(data) {
                    // 顯示原始文字
                    textDisplay.textContent = `原始文字：${data.original_text}`;
                    
                    // 顯示數值表示
                    numericDisplay.textContent = data.numeric_representation;
                    
                    // 顯示質數替換
                    primeDisplay.innerHTML = '';
                    let primeText = '<p>';
                    
                    data.prime_replacements.forEach(word => {
                        if (word.is_prime) {
                            primeText += `<span>${word.original}</span> `;
                        } else if (word.replacements && word.replacements.length > 0) {
                            const replacement = word.replacements[0];
                            primeText += `<span class="prime-text">${replacement.text}</span><span class="distance-indicator">${replacement.direction}${replacement.distance}</span> `;
                        } else {
                            primeText += `<span>${word.original}</span> `;
                        }
                    });
                    
                    primeText += '</p>';
                    primeDisplay.innerHTML = primeText;
                    
                    // 顯示單詞分析
                    wordAnalysis.innerHTML = '';
                    data.prime_replacements.forEach((word, index) => {
                        const wordDiv = document.createElement('div');
                        wordDiv.className = word.is_prime ? 'word-info is-prime' : 'word-info not-prime';
                        
                        let wordContent = `<h4>${word.original} (${word.numeric})</h4>`;
                        if (word.is_prime) {
                            wordContent += `<p><strong>這是一個質數！</strong></p>`;
                        } else {
                            wordContent += `<p>這不是質數</p>`;
                            
                            if (word.replacements && word.replacements.length > 0) {
                                wordContent += `<div class="prime-list"><h5>最接近的質數：</h5>`;
                                
                                word.replacements.forEach(replacement => {
                                    wordContent += `
                                        <div class="prime-item">
                                            <span>${replacement.text} ${replacement.prime}</span>
                                            <span>距離：${replacement.distance} ${replacement.direction}</span>
                                        </div>
                                    `;
                                });
                                
                                wordContent += `</div>`;
                            }
                        }
                        
                        wordDiv.innerHTML = wordContent;
                        wordAnalysis.appendChild(wordDiv);
                    });
                    
                    // 顯示隨機組合
                    combinations.innerHTML = '';
                    data.combinations.forEach((combo, index) => {
                        const comboDiv = document.createElement('div');
                        comboDiv.className = 'combination';
                        
                        let comboText = `<h4>組合 ${index + 1}</h4><p>`;
                        
                        combo.forEach(item => {
                            if (item.is_original) {
                                comboText += `<span>${item.original}</span> `;
                            } else {
                                comboText += `<span class="prime-text">${item.replacement}</span><span class="distance-indicator">${item.direction}${item.distance}</span> `;
                            }
                        });
                        
                        comboText += `</p>`;
                        comboDiv.innerHTML = comboText;
                        combinations.appendChild(comboDiv);
                    });
                    
                    // 顯示結果區域
                    resultsDiv.style.display = 'block';
                }
                
                function showError(message) {
                    errorDiv.textContent = message;
                    errorDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    '''

# 使用 with app.app_context() 預加載 PrimesDB 數據
with app.app_context():
    # 預加載 PrimesDB 數據
    download_primesdb()

if __name__ == '__main__':
    logger.info("Starting 文字與質數的距離 v1.0.0")
    app.run(host='127.0.0.1', port=5004, debug=True)
