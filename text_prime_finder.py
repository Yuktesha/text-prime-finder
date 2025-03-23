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

@app.route('/analyze', methods=['POST'])
def search():
    try:
        data = request.json
        text = data.get('text', '')
        chinese_mode = data.get('chinese_mode', 'auto')
        
        if not text:
            return jsonify({"error": "請提供文字"}), 400
        
        # 解析文字
        parsed_words = parse_text(text, chinese_mode)
        
        # 計算每個單詞的數值並檢查是否為質數
        word_analysis = []
        numeric_values = []
        
        for word in parsed_words:
            numeric_value = word['numeric']
            numeric_values.append(str(numeric_value))
            
            is_prime = word['is_prime']
            closest_prime = None
            distance = None
            
            if not is_prime:
                closest_primes = find_closest_primes(numeric_value, 1)
                if closest_primes and len(closest_primes) > 0:
                    closest_prime = closest_primes[0]['prime']
                    distance = closest_primes[0]['distance']
            
            word_analysis.append({
                "word": word['original'],
                "numeric_value": numeric_value,
                "is_prime": is_prime,
                "closest_prime": closest_prime,
                "distance": distance
            })
        
        return jsonify({
            "original_text": text,
            "numeric_values": numeric_values,
            "word_analysis": word_analysis
        })
        
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}")
        return jsonify({"error": f"處理請求時發生錯誤: {str(e)}"}), 500

def get_index_template():
    """獲取首頁模板"""
    return """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>文字與質數的距離</title>
        <style>
            :root {
                --primary-color: #3b5998;
                --secondary-color: #2c4a7c;
                --accent-color: #4CAF50;
                --error-color: #f44336;
                --border-radius: 8px;
                --box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                --transition: all 0.3s ease;
            }
            
            body {
                font-family: 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            /* 標題樣式 */
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }
            
            .app-title {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 10px;
                font-size: 2rem;
                color: var(--primary-color);
            }
            
            .app-icon {
                margin-right: 10px;
                font-size: 2rem;
            }
            
            .app-description {
                color: #666;
                margin-bottom: 20px;
            }
            
            /* 主要內容區域 */
            .main-content {
                margin-top: 20px;
            }
            
            /* 卡片樣式 */
            .input-section, .result-section {
                background-color: white;
                border-radius: var(--border-radius);
                box-shadow: var(--box-shadow);
                padding: 20px;
                margin-bottom: 20px;
                display: flex;
                flex-direction: column;
            }
            
            /* 表單樣式 */
            .form-group {
                margin-bottom: 0;
            }
            
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #555;
            }
            
            input, select, textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: var(--border-radius);
                font-size: 16px;
                transition: var(--transition);
                box-sizing: border-box;
                background-color: #fff;
            }
            
            input:focus, select:focus, textarea:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 2px rgba(59, 89, 152, 0.2);
            }
            
            /* 修復輸入框紅色邊框問題 */
            input[type="text"] {
                border: 1px solid #ddd;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
                -webkit-appearance: none;
                -moz-appearance: none;
                appearance: none;
            }
            
            input[type="text"]:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 2px rgba(59, 89, 152, 0.2);
            }
            
            input[type="text"]::placeholder {
                color: #aaa;
                opacity: 0.7;
            }
            
            /* 表單佈局 */
            .form-layout {
                display: flex;
                flex-direction: column;
                gap: 15px;
                flex: 1;
            }
            
            /* 按鈕組緊接在表單元素後 */
            .button-group {
                margin-top: 15px;
            }
            
            /* 移動設備優化 */
            @media (max-width: 768px) {
                input[type="text"], select {
                    font-size: 16px; /* 防止iOS縮放 */
                    padding: 12px;
                }
                
                .btn {
                    padding: 12px 20px;
                    width: 100%;
                    margin-right: 0;
                    margin-bottom: 10px;
                }
                
                .button-group {
                    flex-direction: column;
                }
            }
            
            /* 按鈕樣式 */
            .btn {
                display: inline-block;
                padding: 10px 20px;
                background-color: var(--primary-color);
                color: white;
                border: none;
                border-radius: var(--border-radius);
                cursor: pointer;
                font-size: 16px;
                transition: var(--transition);
                margin-right: 10px;
                text-align: center;
            }
            
            .btn:hover {
                background-color: var(--secondary-color);
                transform: translateY(-1px);
            }
            
            /* 按鈕組樣式 */
            .button-group {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            
            .btn-primary {
                background-color: var(--primary-color);
            }
            
            .btn-primary:hover {
                background-color: var(--secondary-color);
            }
            
            .btn-secondary {
                background-color: #6c757d;
            }
            
            .btn-secondary:hover {
                background-color: #5a6268;
            }
            
            /* 移動設備優化 */
            @media (max-width: 768px) {
                body {
                    padding: 15px;
                }
                
                .header {
                    margin-bottom: 20px;
                }
                
                input[type="text"], select, .text-input, .select-input {
                    font-size: 16px; /* 防止iOS縮放 */
                    padding: 12px;
                }
                
                .btn {
                    padding: 12px 20px;
                    width: 100%;
                    margin-right: 0;
                    margin-bottom: 10px;
                }
                
                .button-group {
                    flex-direction: column;
                }
                
                .copy-message {
                    display: block;
                    margin-left: 0;
                    margin-top: 5px;
                }
            }
            
            /* 結果樣式 */
            .result-card {
                background-color: white;
                border-radius: var(--border-radius);
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: var(--box-shadow);
            }
            
            .result-card h3 {
                color: var(--primary-color);
                margin-top: 0;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }
            
            .word-info {
                background-color: #f9f9f9;
                border-radius: var(--border-radius);
                padding: 15px;
                margin-bottom: 15px;
                transition: var(--transition);
            }
            
            .word-info:hover {
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
            }
            
            .word-info h4 {
                margin-top: 0;
                color: var(--dark-color);
            }
            
            .is-prime {
                background-color: rgba(40, 167, 69, 0.1);
                border-left: 4px solid var(--success-color);
            }
            
            .prime-item {
                color: var(--success-color);
                font-weight: 600;
            }
            
            .celebration {
                background-color: #f8f9d7;
                border-radius: var(--border-radius);
                padding: 20px;
                margin: 20px 0;
                text-align: center;
                border: 2px dashed var(--success-color);
                animation: pulse 2s infinite;
                display: none;
            }
            
            .celebration h3 {
                color: var(--success-color);
                margin-top: 0;
            }
            
            .copy-message {
                display: none;
                color: var(--success-color);
                font-size: 14px;
                margin-left: 10px;
                animation: fadeOut 2s forwards;
                animation-delay: 1s;
            }
            
            .action-buttons {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 20px;
            }
            
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.4); }
                70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
                100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
            }
            
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            
            /* 響應式設計 */
            @media (max-width: 768px) {
                .input-section, .result-section {
                    flex: 1 1 100%;
                }
                
                .btn {
                    width: 100%;
                    margin-right: 0;
                }
                
                .action-buttons {
                    flex-direction: column;
                }
                
                .copy-message {
                    display: block;
                    margin-left: 0;
                    margin-top: 5px;
                }
            }
            
            /* 寬螢幕版兩列式設計 */
            @media (min-width: 992px) {
                .main-content {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 30px;
                    align-items: stretch;
                }
                
                .input-section, .result-section {
                    width: 100%;
                    margin: 0;
                    height: auto;
                    min-height: 400px;
                    display: flex;
                    flex-direction: column;
                }
                
                .result-section {
                    max-height: 90vh;
                    overflow-y: auto;
                    padding-bottom: 30px;
                }
                
                .form-layout {
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                    flex: 1;
                }
                
                .button-group {
                    margin-top: auto;
                    padding-top: 20px;
                }
                
                /* 確保結果區域在無內容時也有高度 */
                #result {
                    min-height: 200px;
                }
                
                .result-placeholder {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: var(--border-radius);
                    border: 2px dashed #ddd;
                    margin-bottom: 20px;
                    min-height: 200px;
                }
                
                .result-placeholder h3 {
                    color: var(--primary-color);
                    margin-bottom: 15px;
                    font-size: 1.5rem;
                }
                
                .result-placeholder p {
                    color: #777;
                    font-size: 1.1rem;
                    max-width: 80%;
                    line-height: 1.5;
                }
                
                .result-placeholder::before {
                    content: "📊";
                    font-size: 3rem;
                    margin-bottom: 20px;
                    opacity: 0.7;
                }
            }
            
            .result-placeholder {
                text-align: center;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: var(--border-radius);
                border: 2px dashed #ddd;
                margin-bottom: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 200px;
                flex: 1;
            }
            
            .result-placeholder h3 {
                color: var(--primary-color);
                margin-bottom: 15px;
                font-size: 1.5rem;
            }
            
            .result-placeholder p {
                color: #777;
                font-size: 1.1rem;
                max-width: 80%;
                line-height: 1.5;
            }
            
            .result-placeholder::before {
                content: "📊";
                font-size: 3rem;
                margin-bottom: 20px;
                opacity: 0.7;
            }
            
            /* 工具提示樣式 */
            .tooltip-icon {
                display: inline-block;
                width: 16px;
                height: 16px;
                background-color: var(--primary-color);
                color: white;
                border-radius: 50%;
                text-align: center;
                line-height: 16px;
                font-size: 12px;
                cursor: help;
                margin-left: 5px;
                font-style: normal;
                position: relative;
            }
            
            .tooltip-icon:hover::after {
                content: attr(title);
                position: absolute;
                left: 50%;
                transform: translateX(-50%);
                bottom: 100%;
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                z-index: 10;
                margin-bottom: 5px;
                width: max-content;
                max-width: 300px;
            }
            
            /* 修復輸入框樣式 */
            .text-input {
                border: 1px solid #ddd !important;
                outline: none !important;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05) !important;
                -webkit-appearance: none !important;
                -moz-appearance: none !important;
                appearance: none !important;
                border-radius: var(--border-radius) !important;
                background-color: #fff !important;
            }
            
            .text-input:focus {
                border-color: var(--primary-color) !important;
                box-shadow: 0 0 0 2px rgba(59, 89, 152, 0.2) !important;
            }
            
            .text-input::placeholder {
                color: #aaa !important;
                opacity: 0.7 !important;
            }
            
            /* 修復下拉選單樣式 */
            .select-input {
                border: 1px solid #ddd !important;
                outline: none !important;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05) !important;
                -webkit-appearance: none !important;
                -moz-appearance: none !important;
                appearance: none !important;
                border-radius: var(--border-radius) !important;
                background-color: #fff !important;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23333' d='M6 8.825L1.175 4 2.05 3.125 6 7.075 9.95 3.125 10.825 4z'/%3E%3C/svg%3E");
                background-repeat: no-repeat !important;
                background-position: right 10px center !important;
                padding-right: 30px !important;
            }
            
            .select-input:focus {
                border-color: var(--primary-color) !important;
                box-shadow: 0 0 0 2px rgba(59, 89, 152, 0.2) !important;
            }
            
            /* 文本區域樣式 */
            textarea.text-input {
                resize: vertical;
                min-height: 100px;
                flex: 1;
                margin-bottom: 15px;
                border: 1px solid #ddd !important;
                outline: none !important;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05) !important;
                -webkit-appearance: none !important;
                -moz-appearance: none !important;
                appearance: none !important;
                border-radius: var(--border-radius) !important;
                background-color: #fff !important;
                font-family: inherit;
                line-height: 1.5;
            }
            
            textarea.text-input:focus {
                border-color: var(--primary-color) !important;
                box-shadow: 0 0 0 2px rgba(59, 89, 152, 0.2) !important;
            }
            
            .footer {
                text-align: center;
                padding: 20px;
                margin-top: 40px;
                color: #666;
                font-size: 14px;
                border-top: 1px solid #eee;
            }
            
            .footer a {
                color: var(--primary-color);
                text-decoration: none;
            }
            
            .footer a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1>🔢 文字與質數的距離 🧮</h1>
                <p>輸入文字，計算其數值並找出最接近的質數</p>
            </header>
            
            <div class="main-content">
                <section class="input-section">
                    <form id="text_form" class="form-layout">
                        <div class="form-group">
                            <label for="text">輸入文字：</label>
                            <textarea id="text" name="text" placeholder="例如：Hello 或 你好" class="text-input" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="chinese_mode">中文處理模式：
                                <span class="tooltip-icon" title="自動：使用jieba智能識別中文詞彙；按字符：將每個中文字符視為獨立單元；按空格：使用空格作為分隔符">ⓘ</span>
                            </label>
                            <select id="chinese_mode" name="chinese_mode" class="select-input">
                                <option value="auto">自動（使用jieba）</option>
                                <option value="char">按字符處理</option>
                                <option value="space">按空格分隔</option>
                            </select>
                        </div>
                        
                        <div class="button-group">
                            <button type="submit" class="btn btn-primary">計算</button>
                            <button type="button" id="clear_btn" class="btn btn-secondary">清除</button>
                        </div>
                    </form>
                </section>
                
                <section class="result-section">
                    <div class="result-placeholder" id="result_placeholder">
                        <h3>計算結果將顯示在這裡</h3>
                        <p>請在左側輸入文字並點擊「計算」按鈕</p>
                    </div>
                    <div id="result" style="display: none;">
                        <div class="result-card">
                            <h3>計算結果</h3>
                            <div id="prime_result"></div>
                            <div class="action-buttons">
                                <button id="copy_prime_btn" class="btn btn-copy">複製數值</button>
                                <button id="copy_analysis_btn" class="btn btn-copy">複製分析結果</button>
                                <button id="export_csv_btn" class="btn btn-copy">導出為CSV</button>
                                <span class="copy-message">已複製！</span>
                            </div>
                        </div>
                        
                        <div id="celebration" class="celebration">
                            <h3>🎉 恭喜！你找到了質數！🎉</h3>
                            <p>你輸入的文字包含質數，這是質人精神的體現！</p>
                        </div>
                        
                        <div class="result-card">
                            <h3>單詞分析</h3>
                            <div id="word_analysis"></div>
                        </div>
                    </div>
                </section>
            </div>
            
            <footer class="footer">
                <p>© 2025 質人精神：文字與質數的距離 | 基於<a href="https://github.com/pekesoft/PrimesDB" target="_blank">PrimesDB</a>高效質數資料庫的應用</p>
            </footer>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const form = document.getElementById('text_form');
                const textInput = document.getElementById('text');
                const chineseModeSelect = document.getElementById('chinese_mode');
                const clearBtn = document.getElementById('clear_btn');
                const resultDiv = document.getElementById('result');
                const resultPlaceholder = document.getElementById('result_placeholder');
                const primeResultDiv = document.getElementById('prime_result');
                const wordAnalysisDiv = document.getElementById('word_analysis');
                const celebrationDiv = document.getElementById('celebration');
                const copyPrimeBtn = document.getElementById('copy_prime_btn');
                const copyAnalysisBtn = document.getElementById('copy_analysis_btn');
                const exportCsvBtn = document.getElementById('export_csv_btn');
                
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const text = textInput.value.trim();
                    if (!text) {
                        alert('請輸入文字');
                        return;
                    }
                    
                    const chineseMode = chineseModeSelect.value;
                    
                    // 顯示加載中
                    resultDiv.style.display = 'none';
                    resultPlaceholder.style.display = 'none';
                    primeResultDiv.innerHTML = '<p>計算中...</p>';
                    
                    // 發送請求
                    fetch('/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            text: text,
                            chinese_mode: chineseMode
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        // 顯示結果
                        resultDiv.style.display = 'block';
                        resultPlaceholder.style.display = 'none';
                        
                        // 顯示計算結果
                        let primeResultHtml = '';
                        if (data.numeric_values) {
                            primeResultHtml += `<p>原始文字：<strong>${data.original_text}</strong></p>`;
                            primeResultHtml += `<p>數值表示：<strong>${data.numeric_values.join(' ')}</strong></p>`;
                        }
                        primeResultDiv.innerHTML = primeResultHtml;
                        
                        // 顯示單詞分析
                        let wordAnalysisHtml = '';
                        let hasPrime = false;
                        
                        if (data.word_analysis) {
                            data.word_analysis.forEach(word => {
                                const isPrime = word.is_prime;
                                if (isPrime) hasPrime = true;
                                
                                wordAnalysisHtml += `<div class="word-info ${isPrime ? 'is-prime' : ''}">`;
                                wordAnalysisHtml += `<h4>${word.word} (${word.numeric_value})</h4>`;
                                
                                if (isPrime) {
                                    wordAnalysisHtml += `<p class="prime-item">🎉 這是一個質數！</p>`;
                                } else if (word.closest_prime) {
                                    wordAnalysisHtml += `<p class="prime-item">${word.closest_prime} (距離：${word.distance})</p>`;
                                }
                                
                                wordAnalysisHtml += '</div>';
                            });
                        }
                        
                        wordAnalysisDiv.innerHTML = wordAnalysisHtml;
                        
                        // 如果有質數，顯示慶祝訊息
                        celebrationDiv.style.display = hasPrime ? 'block' : 'none';
                        
                        // 滾動到結果區域
                        resultDiv.scrollIntoView({ behavior: 'smooth' });
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        primeResultDiv.innerHTML = '<p class="error">發生錯誤，請稍後再試</p>';
                        resultDiv.style.display = 'block';
                        resultPlaceholder.style.display = 'none';
                    });
                });
                
                // 清除按鈕
                clearBtn.addEventListener('click', function() {
                    textInput.value = '';
                    resultDiv.style.display = 'none';
                    resultPlaceholder.style.display = 'block';
                    textInput.focus();
                });
                
                // 複製到剪貼簿函數
                function copyToClipboard(text) {
                    if (navigator.clipboard) {
                        navigator.clipboard.writeText(text)
                            .catch(err => {
                                console.error('無法複製: ', err);
                            });
                    } else {
                        const textarea = document.createElement('textarea');
                        textarea.value = text;
                        textarea.style.position = 'fixed';
                        document.body.appendChild(textarea);
                        textarea.select();
                        try {
                            document.execCommand('copy');
                        } catch (err) {
                            console.error('無法複製: ', err);
                        }
                        document.body.removeChild(textarea);
                    }
                }
                
                // 顯示複製成功訊息
                function showCopyMessage(button) {
                    const message = button.nextElementSibling;
                    if (message && message.classList.contains('copy-message')) {
                        message.style.display = 'inline';
                        message.style.opacity = '1';
                        setTimeout(() => {
                            message.style.opacity = '0';
                            setTimeout(() => {
                                message.style.display = 'none';
                            }, 1000);
                        }, 1000);
                    }
                }
                
                // 複製數值按鈕
                copyPrimeBtn.addEventListener('click', function() {
                    const textOnly = primeResultDiv.textContent.replace(/\\s+/g, ' ').trim();
                    copyToClipboard(textOnly);
                    showCopyMessage(this);
                });
                
                // 複製分析結果按鈕
                copyAnalysisBtn.addEventListener('click', function() {
                    let analysisText = '';
                    document.querySelectorAll('#word_analysis .word-info').forEach(wordDiv => {
                        analysisText += wordDiv.textContent.replace(/\\s+/g, ' ').trim() + '\\n\\n';
                    });
                    copyToClipboard(analysisText);
                    showCopyMessage(this);
                });
                
                // 導出為CSV按鈕
                exportCsvBtn.addEventListener('click', function() {
                    let csvContent = '原始文字,數值,是否質數,最接近質數,距離\\n';
                    
                    document.querySelectorAll('#word_analysis .word-info').forEach(wordDiv => {
                        const title = wordDiv.querySelector('h4').textContent;
                        const isPrime = wordDiv.classList.contains('is-prime');
                        const original = title.split(' ')[0];
                        const numeric = title.match(/\\((\\d+)\\)/)[1];
                        
                        let closestPrime = '';
                        let distance = '';
                        
                        if (!isPrime && wordDiv.querySelector('.prime-item')) {
                            const primeInfo = wordDiv.querySelector('.prime-item').textContent.trim();
                            closestPrime = primeInfo.split(' ')[0];
                            distance = primeInfo.match(/距離：(\\d+)/)[1];
                        }
                        
                        csvContent += `"${original}","${numeric}","${isPrime ? '是' : '否'}","${closestPrime}","${distance}"\\n`;
                    });
                    
                    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.setAttribute('href', url);
                    link.setAttribute('download', '文字質數分析.csv');
                    link.style.visibility = 'hidden';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    showCopyMessage(this);
                });
            });
        </script>
    </body>
    </html>
    """

# 使用 with app.app_context() 預加載 PrimesDB 數據
with app.app_context():
    # 預加載 PrimesDB 數據
    download_primesdb()

if __name__ == '__main__':
    logger.info("Starting 文字與質數的距離 v1.0.0")
    app.run(host='127.0.0.1', port=5004, debug=True)
