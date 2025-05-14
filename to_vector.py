import os
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from tqdm import tqdm
from sklearn.base import BaseEstimator, TransformerMixin
import re
from datetime import datetime

# 配置路径
DATA_DIR = "/Users/mac/Desktop/risk-management/filtered_companys_adjusted"

class RiskDataProcessor:
    def __init__(self):
        # 定义字段映射
        self.field_structure = {
            'number': [
                "上市信息->企业简介->年结日",
                "上市信息->企业简介->注册资本",
                "工商信息->工商信息->成立日期",
                "工商信息->工商信息->核准日期",
                "工商信息->工商信息->营业期限"
            ],
            'category': [
                "工商信息->工商信息->人员规模",
                "工商信息->工商信息->登记状态",
                "工商信息->工商信息->纳税人资质"
            ],
            'text': [
                "上市信息->证券信息",
                "工商信息->工商信息->企业名称",
                "工商信息->工商信息->登记机关",
                "工商信息->工商信息->经营范围",
                "法律诉讼->限制出境",
                "经营风险->担保风险"
            ]
        }
        # 在原有代码中的集成方式
        num_pipeline = Pipeline([
            ('preprocessor', NumberPreprocessor()),  # 新增预处理步骤
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        # 初始化转换器
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', 
                 num_pipeline, 
                 self._get_field_names('number')),

                # 采用独热编码处理分类
                ('cat', 
                 Pipeline([
                    ('imputer', SimpleImputer(strategy='constant', 
                                              fill_value='unknown',
                                              missing_values=np.nan)), # 缺失值填充
                    ('onehot', OneHotEncoder(handle_unknown='ignore')) # 独热编码
                ]), 
                self._get_field_names('category')),

                # 将多列文本数据合并为一列，然后将文本转换为TF-IDF特征矩阵
                (
                'txt',  # 流水线名称标识符
                Pipeline([  # 嵌套处理流程
                    ('combiner', TextCombiner()),  # 第一步：文本字段合并
                    ('tfidf', TfidfVectorizer(max_features=500))  # 第二步：TF-IDF向量化
                ]),
                self._get_field_names('text')  # 指定处理的字段列表
                )
            ])
        

    def _get_field_names(self, data_type):
        """获取指定类型的字段路径列表"""
        return self.field_structure[data_type]

    def load_single_company(self, file_path):
        """加载单个公司数据"""
        data = {}
        for dtype in ['number', 'category', 'text']:
            # 构建完整路径：如 "number/公司A_number.json"
            full_path = os.path.join(DATA_DIR, dtype, f"{file_path.split('_')[0]}_{dtype}.json")
            with open(full_path,'r') as f:
                data.update(json.load(f))
        return data

    def create_dataset(self):
        """创建完整数据集"""
        # 获取所有公司文件，从 DATA_DIR/number 目录中获取所有 JSON 文件名
        company_files = [f for f in os.listdir(os.path.join(DATA_DIR, 'number')) 
                        if f.endswith('.json')]
        
        # 构建DataFrame
        df = pd.DataFrame()
        for cf in tqdm(company_files, desc="Loading Data"):
            company_data = self.load_single_company(cf)
            df = pd.concat([df, pd.DataFrame([company_data])], ignore_index=True)
        
        return df

    def process_labels(self, y):
        """转换风险评级标签"""
        bins = [-np.inf, 50, 65, 80, np.inf]
        labels = ['D', 'C', 'B', 'A']
        # 通过 pd.cut 将连续数值按预设区间划分，并映射为指定标签
        return pd.cut(y, bins=bins, labels=labels)

    def get_feature_pipeline(self):
        """获取特征处理流水线"""
        return self.preprocessor


class NumberPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.date_ref = datetime.now().year  # 当前年份作为参考
    
    def fit(self, X, y=None):
        # 学习必要参数（如中位数等）
        self.capital_median_ = None
        return self
    
    def transform(self, X):
        return X.apply(self._process_row, axis=1)
    
    def _process_row(self, row):
        processed = {}
        
        # 处理日期字段
        processed['成立年限'] = self._parse_date(row["工商信息->工商信息->成立日期"])
        processed['核准年数'] = self._parse_date(row["工商信息->工商信息->核准日期"])
        processed['剩余营业年'] = self._parse_duration(row["工商信息->工商信息->营业期限"])
        
        # 处理带单位数值
        processed['注册资本(万)'] = self._parse_capital(row["上市信息->企业简介->注册资本"])
        
        # 处理特殊空值
        processed['年结日'] = 1 if pd.isnull(row["上市信息->企业简介->年结日"]) else 0
        
        return pd.Series(processed)
    
    
    def _parse_date(self, date_str):
        """解析日期为年限"""
        if not date_str or pd.isnull(date_str):
            return np.nan
        try:
            year = datetime.strptime(date_str, "%Y-%m-%d").year
            return self.date_ref - year
        except:
            return np.nan
    
    def _parse_duration(self, duration_str):
        """计算剩余营业年限"""
        if not duration_str or pd.isnull(duration_str):
            return np.nan
        try:
            end_date = datetime.strptime(duration_str.split(',')[1], "%Y-%m-%d")
            return end_date.year - self.date_ref
        except:
            return np.nan
    
    def _parse_capital(self, capital_str):
        """提取注册资本数值"""
        if not capital_str or pd.isnull(capital_str):
            return np.nan
        match = re.search(r'(\d+\.?\d*)', capital_str)
        return float(match.group(1)) if match else np.nan



# 自定义文本组合器
class TextCombiner(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return X.apply(lambda row: ' '.join(row.values.astype(str)), axis=1)
    
    def get_feature_names_out(self, input_features=None):
        return ['combined_text']  # 或直接 pass，交由后续 TfidfVectorizer 处理

if __name__ == "__main__":
    # 初始化处理器
    processor = RiskDataProcessor()
    
    # 加载数据集
    df = processor.create_dataset()
    
    # 提取特征和标签
    y = processor.process_labels(df["工商信息->工商信息->天眼评分"])
    X = df.drop("工商信息->工商信息->天眼评分", axis=1)
    

    # 执行特征转换
    X_transformed = processor.get_feature_pipeline().fit_transform(X)

    print("特征矩阵形状:", X_transformed.shape)
    # 打印类型
    print("特征矩阵类型:", type(X_transformed))
    # 打印头部
    print("特征矩阵:\n", X_transformed[0])
    print("标签分布:\n", y.value_counts())
    # # 合并时不保留列名
    merged_array = np.hstack((X_transformed.toarray(), y.values.reshape(-1, 1)))
    np.savetxt('risk-management/features_with_labels.csv', merged_array, delimiter=',', fmt='%s')