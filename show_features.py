import os
import json
from collections import defaultdict
from tqdm import tqdm

INPUT_DIR = "/Users/mac/Desktop/risk-management/filtered_companys_adjusted"
OUTPUT_FILE = os.path.join(INPUT_DIR, "common_fields.json")

class FieldAnalyzer:
    def __init__(self):
        self.categories = ['number', 'category', 'text']
        self.field_counter = defaultdict(lambda: defaultdict(int))
        self.total_companies = 0

    def analyze_fields(self):
        """分析所有公司的公共字段"""
        # 获取所有公司基础名称
        companies = self._get_company_list()
        self.total_companies = len(companies)

        # 遍历每个公司收集字段
        for company in tqdm(companies, desc="Analyzing Companies"):
            for cat in self.categories:
                self._process_company_category(company, cat)

        # 计算公共字段
        return self._calculate_common_fields()

    def _get_company_list(self):
        """获取公司列表（任一分类目录均可）"""
        return list({
            f.split('_number.json')[0]
            for f in os.listdir(os.path.join(INPUT_DIR, 'number'))
            if f.endswith('.json')
        })

    def _process_company_category(self, company, category):
        """处理单个分类文件"""
        file_path = os.path.join(INPUT_DIR, category, f"{company}_{category}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for field in data.keys():
                    self.field_counter[category][field] += 1
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    def _calculate_common_fields(self):
        """计算跨公司公共字段"""
        common_fields = {}
        for cat in self.categories:
            common = [
                field for field, count in self.field_counter[cat].items()
                if count == self.total_companies
            ]
            common_fields[cat] = sorted(common)
        return common_fields

    def save_results(self, common_fields):
        """保存公共字段配置"""
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(common_fields, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    analyzer = FieldAnalyzer()
    result = analyzer.analyze_fields()
    analyzer.save_results(result)
    
    print("\n新版公共字段配置文件已生成：")
    print(f"路径：{OUTPUT_FILE}")
    print("各分类公共字段数量统计：")
    for cat, fields in result.items():
        print(f"{cat.upper()}: {len(fields)} 个字段")