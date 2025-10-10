# app/matcher.py
# (这里放置我们之前完成的 MaterialMatcher 完整代码)
# --- 为了简洁，这里仅展示类的定义，内容与之前一致 ---
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

class MaterialMatcher:
    # ... (此处省略我们上一轮已完成的完整代码)
    def __init__(self, df_master, rules):
        if df_master.empty:
            raise ValueError("主数据 DataFrame 不能为空")
            
        self.rules = rules
        self.master_fields = rules['master_fields']
        self.df_master = self._preprocess(df_master.copy(), self.master_fields)
        
        self.fuzzy_text_col = '_fuzzy_text'
        self.df_master[self.fuzzy_text_col] = self.df_master[self.master_fields['fuzzy']].apply(
            lambda x: ' '.join(x.astype(str)), axis=1
        )
        
        self.vectorizer = TfidfVectorizer()
        self.tfidf_master = self.vectorizer.fit_transform(self.df_master[self.fuzzy_text_col])
        
        logging.info("MaterialMatcher 初始化完成。")

    def _preprocess(self, df, fields_map):
        all_fields = fields_map['exact'] + fields_map['fuzzy']
        for col in all_fields:
            if col not in df.columns:
                raise ValueError(f"规则中定义的列 '{col}' 在主数据中不存在。")
            df[col] = df[col].fillna('').astype(str)
        return df

    def find_matches(self, new_item_series, top_n=3):
        new_item_fields = self.rules['new_item_fields']
        
        candidate_df = self.df_master.copy()
        for i, field in enumerate(self.master_fields['exact']):
            new_item_exact_field = new_item_fields['exact'][i]
            exact_value = new_item_series.get(new_item_exact_field, '')
            if pd.notna(exact_value) and str(exact_value).strip() != '':
                candidate_df = candidate_df[candidate_df[field] == str(exact_value)]
        
        if candidate_df.empty:
            return pd.DataFrame()

        new_item_fuzzy_text_parts = [str(new_item_series.get(f, '')) for f in new_item_fields['fuzzy']]
        new_item_fuzzy_text = ' '.join(new_item_fuzzy_text_parts)
        
        new_item_vector = self.vectorizer.transform([new_item_fuzzy_text])
        
        candidate_indices = candidate_df.index
        candidate_vectors = self.tfidf_master[candidate_indices]
        
        similarities = cosine_similarity(new_item_vector, candidate_vectors)
        
        candidate_df['similarity'] = similarities.flatten()
        
        results = candidate_df.sort_values(by='similarity', ascending=False).head(top_n)
        
        return results