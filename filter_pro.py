import os
import json
from collections import defaultdict
from tqdm import tqdm

'''
只取所有公司共有的片段
'''

CLEAN_DATA_DIR = "/Users/mac/Desktop/risk-management/filtered_companys"
PROCESSED_DIR = "/Users/mac/Desktop/risk-management/filtered_companys_pro"
OUTPUT_FILE = os.path.join(CLEAN_DATA_DIR, "common_fields.json")
COMMON_FIELDS_FILE = os.path.join(CLEAN_DATA_DIR, "common_fields.json")


class FieldAnalyzer:
    def __init__(self):
        self.categories = ['number', 'category', 'text']
        self.field_counter = defaultdict(lambda: defaultdict(set))
        self.total_companies = 0

    def analyze_fields(self):
        """分析所有公司的字段"""
        # 获取所有公司列表
        base_names = self._get_company_base_names()
        self.total_companies = len(base_names)

        # 遍历每个公司收集字段
        for base in tqdm(base_names, desc="Analyzing Companies"):
            for cat in self.categories:
                file_path = os.path.join(CLEAN_DATA_DIR, cat, f"{base}_{cat}.json")
                self._process_file(file_path, cat)

        # 计算公共字段
        return self._calculate_common_fields()

    def _get_company_base_names(self):
        """获取所有公司基础名称"""
        number_dir = os.path.join(CLEAN_DATA_DIR, 'number')
        return [f.split('_number')[0] for f in os.listdir(number_dir) if f.endswith('.json')]

    def _process_file(self, file_path, category):
        """处理单个分类文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 过滤并收集有效字段
            valid_fields = {k for k in data.keys() if '[' and ']' not in k}
            self.field_counter[category][file_path] = valid_fields
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    def _calculate_common_fields(self):
        """计算跨公司的公共字段"""
        common_fields = {cat: None for cat in self.categories}

        for cat in self.categories:
            # 获取该分类下所有公司的字段集合
            all_field_sets = list(self.field_counter[cat].values())
            
            if not all_field_sets:
                continue

            # 计算交集
            common = set.intersection(*all_field_sets)
            common_fields[cat] = sorted(common)

        return common_fields

    def save_results(self, common_fields):
        """保存最终结果"""
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(common_fields, f, ensure_ascii=False, indent=2)

def load_common_fields():
    """加载公共字段配置"""
    with open(COMMON_FIELDS_FILE, 'r', encoding='utf-8') as f:
        common_fields = json.load(f)
    return {
        'number': set(common_fields['number']),
        'category': set(common_fields['category']),
        'text': set(common_fields['text'])
    }

def process_company_files(common_sets):
    """处理所有公司文件"""
    # 创建输出目录
    for data_type in ['number', 'category', 'text']:
        os.makedirs(os.path.join(PROCESSED_DIR, data_type), exist_ok=True)

    # 获取所有公司基础名称
    base_names = {
        f.split('_number.json')[0] 
        for f in os.listdir(os.path.join(CLEAN_DATA_DIR, 'number'))
        if f.endswith('.json')
    }

    # 处理每个公司
    for base in tqdm(base_names, desc="Processing Companies"):
        for data_type in ['number', 'category', 'text']:
            # 原始文件路径
            src_file = os.path.join(
                CLEAN_DATA_DIR, data_type, f"{base}_{data_type}.json"
            )
            
            # 目标文件路径
            dest_file = os.path.join(
                PROCESSED_DIR, data_type, f"{base}_{data_type}.json"
            )
            
            # 执行字段过滤
            filter_fields(src_file, dest_file, common_sets[data_type])

def filter_fields(input_path, output_path, allowed_fields):
    """执行字段过滤操作"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # 筛选有效字段
        filtered_data = {
            k: v for k, v in original_data.items()
            if k in allowed_fields
        }
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")

if __name__ == "__main__":
    # 筛选出公共字段
    # analyzer = FieldAnalyzer()
    # result = analyzer.analyze_fields()
    # analyzer.save_results(result)
    
    # print("公共字段分析完成！结果已保存至：")
    # print(f"-> {OUTPUT_FILE}")
    # print("\n各分类公共字段数量：")
    # for cat, fields in result.items():
    #     print(f"{cat.upper()}: {len(fields)} 个")

    # 保留公共 字段
    field_sets = load_common_fields()
    
    # 执行处理流程
    process_company_files(field_sets)
    
    print(f"\n处理完成！标准化数据已保存至：{PROCESSED_DIR}")
    print("各分类保留字段数量：")
    for k, v in field_sets.items():
        print(f"{k.upper()}: {len(v)} 个")