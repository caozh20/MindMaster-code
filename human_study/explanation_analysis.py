import sqlite3
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import jieba
import os

# Connect to database
conn = sqlite3.connect('db/database.db')

# Query all relevant columns
query = """
SELECT game_id, scenario, user_id, user_name, user_agent_id, iteration, 
       running_status, estimation_explanation, intention_explanation, action_explanation 
FROM user_interaction
"""
df = pd.read_sql_query(query, conn)

# Create results directory if it doesn't exist
if not os.path.exists('results'):
    os.makedirs('results')

# Export raw data to Excel
df.to_excel('results/user_interactions.xlsx', index=False)

# Analysis function
def analyze_field(field_name, series):
    total_count = len(series)
    non_null_count = series.notna().sum()
    non_null_pct = (non_null_count / total_count) * 100
    
    # Calculate character and word counts for non-null values
    non_null_texts = series[series.notna()]
    avg_char_length = non_null_texts.str.len().mean()
    
    # Calculate word counts (split English by space, use jieba for Chinese)
    word_counts = []
    for text in non_null_texts:
        # Use jieba to segment Chinese text while preserving English words
        words = list(jieba.cut(text))
        word_counts.append(len(words))
    avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
    
    print(f"\nAnalysis for {field_name}:")
    print(f"Total records: {total_count}")
    print(f"Non-null records: {non_null_count} ({non_null_pct:.1f}%)")
    print(f"Average length: {avg_char_length:.1f} characters")
    print(f"Average word count: {avg_word_count:.1f} words")
    
    # Generate wordcloud with Chinese support
    if non_null_count > 0:
        # Combine all non-null text and segment with jieba
        text = ' '.join(non_null_texts)
        segmented_text = ' '.join(jieba.cut(text))
        # print(segmented_text)
        # Create and generate wordcloud with Chinese font
        wordcloud = WordCloud(
            font_path='C:\Windows\Fonts\simhei.ttf',  # Specify a Chinese font file
            width=800, 
            height=400,
            background_color='white'
        ).generate(segmented_text)
        
        # Display wordcloud
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Word Cloud - {field_name}')
        plt.savefig(f'results/wordcloud_{field_name.lower()}.png')
        plt.close()

# Analyze each explanation field
for field in ['estimation_explanation', 'intention_explanation', 'action_explanation']:
    analyze_field(field, df[field])

conn.close()
