import os
import json
import re
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor

'''
对文件进行处理 ，得到每个公司的 number、category、text 三个分类，拆分出递归
'''

# 配置路径
RAW_DATA_DIR = "/Users/mac/Desktop/risk-management/companys"
CLEAN_DATA_DIR = "/Users/mac/Desktop/risk-management/filtered_companys"

# 初始化日志
logging.basicConfig(
    filename=os.path.join(CLEAN_DATA_DIR, 'processing.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CompanyDataProcessor:
    def __init__(self):
        self.html_pattern = re.compile(r'<[^>]+>')
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$\$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        self.number_pattern = re.compile(r'''
            (^\d{4}-\d{2}-\d{2}$)|               # 日期格式
            (^\d+\.?\d*%?万?元?$)|               # 数值/金额
            (^(?:[1-9]\d{0,2}(,\d{3})*|\d+)(\.\d+)?$)|  # 数字格式
            (^[0-9.,]+$)
        ''', re.X)

    def process_all_files(self):
        """批量处理目录下所有文件"""
        os.makedirs(CLEAN_DATA_DIR, exist_ok=True)
        files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.txt')]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(tqdm(
                executor.map(self.process_single_file, files),
                total=len(files),
                desc="Processing Files"
            ))

    def process_single_file(self, filename):
        """处理单个公司文件"""
        try:
            # 读取原始数据
            with open(os.path.join(RAW_DATA_DIR, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 清洗数据
            cleaned_data = self.recursive_clean(data)
            
            # 分类数据
            classified = self.classify_data(cleaned_data)
            
            # 保存结果
            self.save_results(filename, classified)
            
            logging.info(f"Successfully processed {filename}")
        except Exception as e:
            logging.error(f"Failed to process {filename}: {str(e)}")

    def recursive_clean(self, data):
        """递归清洗数据结构"""
        if isinstance(data, dict):
            return {k: self.recursive_clean(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.recursive_clean(item) for item in data]
        elif isinstance(data, str):
            return self.clean_text(data)
        return data

    def clean_text(self, text):
        """文本清洗"""
        cleaned = self.html_pattern.sub('', text)
        cleaned = self.url_pattern.sub('', cleaned)
        return cleaned.strip()

    def classify_data(self, data):
        """数据分类"""
        classified = {'number': {}, 'category': {}, 'text': {}}
        self.traverse_data(data, [], classified)
        return classified

    def traverse_data(self, data, path, classified):
        """递归遍历数据结构"""
        if isinstance(data, dict):
            for k, v in data.items():
                self.traverse_data(v, path + [k], classified)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self.traverse_data(item, path + [f'[{i}]'], classified)
        else:
            field_type = self.determine_field_type(data)
            key_path = '->'.join(path)
            classified[field_type][key_path] = data

    def determine_field_type(self, value):
        """判断字段类型"""
        if isinstance(value, (int, float)):
            return 'number'
        if isinstance(value, str):
            if self.number_pattern.match(value):
                return 'number'
            if len(value) < 50 and '、' not in value and ' ' not in value:
                return 'category'
        return 'text'

    def save_results(self, filename, classified):
        """保存分类结果"""
        base_name = os.path.splitext(filename)[0]
        
        for data_type in ['number', 'category', 'text']:
            output_dir = os.path.join(CLEAN_DATA_DIR, data_type)
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, f"{base_name}_{data_type}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(classified[data_type], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    processor = CompanyDataProcessor()
    processor.process_all_files()
    print(f"处理完成！清洗后的数据已保存至：{CLEAN_DATA_DIR}")