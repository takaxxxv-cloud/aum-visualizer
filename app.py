import streamlit as st
import pandas as pd
import plotly.express as px

# データの読み込み
@st.cache_data
def load_member_data():
    # 本来はDBやGoogle Sheetsから読み込む想定
    df = pd.read_csv('data/member_data.csv')
    
    # 日付型に変換
    df['pre_reg_at'] = pd.to_datetime(df['pre_reg_at'])
    df['main_reg_at'] = pd.to_datetime(df['main_reg_at'])
    
    # 月単位の列を作成 (例: 2025-01)
    df['pre_month'] = df['pre_reg_at'].dt.to_period('M').astype(str)
    df['main_month'] = df['main_reg_at'].dt.to_period('M').astype(str)
    
    return df

df_members = load_member_data()

# --- 集計処理 ---
# 仮登録数の月別集計
pre_counts = df_members.groupby('pre_month').size().reset_index(name='仮登録数')
pre_counts.columns = ['month', '仮登録数']

# 本登録数の月別集計（空欄を除外して集計）
main_counts = df_members.dropna(subset=['main_reg_at']).groupby('main_month').size().reset_index(name='本登録数')
main_counts.columns = ['month', '本登録数']

# 2つのデータを結合
stats_df = pd.merge(pre_counts, main_counts, on='month', how='outer').fillna(0)
stats_df = stats_df.sort_values('month')

# 累計の計算
stats_df['累計仮登録数'] = stats_df['仮登録数'].cumsum()
stats_df['累計本登録数'] = stats_df['本登録数'].cumsum()

# --- UI表示 ---
st.title("👥 会員登録状況分析")

# 指標の表示
col1, col2 = st.columns(2)
col1.metric("総本登録数", f"{stats_df['本登録数'].sum():,.0f} 名")
col2.metric("本登録CVR", f"{(stats_df['本登録数'].sum() / stats_df['仮登録数'].sum())*100:.1f} %")

# グラフ化
fig = px.bar(stats_df, x='month', y=['仮登録数', '本登録数'], 
             title="月次登録推移", barmode='group')
st.plotly_chart(fig, use_container_width=True)

st.subheader("累計推移")
fig_cum = px.line(stats_df, x='month', y=['累計仮登録数', '累計本登録数'], markers=True)
st.plotly_chart(fig_cum, use_container_width=True)
