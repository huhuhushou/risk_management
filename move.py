import os
import json
from tqdm import tqdm

'''
移动字段到对应的分类中，同时删除一些不必要的字段 
'''

# 配置路径
INPUT_DIR = "/Users/mac/Desktop/risk-management/filtered_companys_pro"
OUTPUT_DIR = "/Users/mac/Desktop/risk-management/filtered_companys_adjusted"
CATEGORY_ADJUSTMENTS = {
    # 需要移动到number的字段
    'number': {
        "上市信息->企业简介->年结日",
        "上市信息->企业简介->注册资本",
        "工商信息->工商信息->营业期限"
    },
    # 需要保留在category的字段
    'category': {
        "工商信息->工商信息->人员规模",
        "工商信息->工商信息->登记状态",
        "工商信息->工商信息->纳税人资质"
    },
    # 需要移动到text的字段
    'text': {
        "工商信息->工商信息->企业名称",
        "工商信息->工商信息->登记机关",
        "法律诉讼->限制出境",
        "经营风险->担保风险"
    }
}

def process_companies():
    # 创建输出目录
    for dtype in ['number', 'category', 'text']:
        os.makedirs(os.path.join(OUTPUT_DIR, dtype), exist_ok=True)

    # 获取所有公司列表
    companies = set()
    for f in os.listdir(os.path.join(INPUT_DIR, 'category')):
        if f.endswith('.json'):
            companies.add(f.split('_category.json')[0])

    # 处理每个公司
    for company in tqdm(companies, desc="Adjusting Categories"):
        try:
            # 加载原始数据
            original_data = {}
            for dtype in ['number', 'category', 'text']:
                file_path = os.path.join(INPUT_DIR, dtype, f"{company}_{dtype}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_data[dtype] = json.load(f)

            # 初始化新数据结构
            adjusted_data = {
                'number': original_data.get('number', {}).copy(),
                'category': {},
                'text': original_data.get('text', {}).copy()
            }

            # 处理category字段
            for field, value in original_data.get('category', {}).items():
                if field in CATEGORY_ADJUSTMENTS['number']:
                    adjusted_data['number'][field] = value
                elif field in CATEGORY_ADJUSTMENTS['text']:
                    adjusted_data['text'][field] = value
                elif field in CATEGORY_ADJUSTMENTS['category']:
                    adjusted_data['category'][field] = value
                else:
                    # 未明确指定的字段默认保留在category
                    adjusted_data['category'][field] = value

            # 保存结果
            for dtype in ['number', 'category', 'text']:
                output_path = os.path.join(OUTPUT_DIR, dtype, f"{company}_{dtype}.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(adjusted_data[dtype], f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"\n处理 {company} 时发生错误: {str(e)}")

if __name__ == "__main__":
    process_companies()
    print(f"\n分类调整完成！结果已保存至：{OUTPUT_DIR}")
    print("最终字段分布：")
    print("Number:   ", len(CATEGORY_ADJUSTMENTS['number']), "个字段")
    print("Category: ", len(CATEGORY_ADJUSTMENTS['category']), "个字段")
    print("Text:     ", len(CATEGORY_ADJUSTMENTS['text']), "个字段")