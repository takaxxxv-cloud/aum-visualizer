import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Fund Analysis Tool", layout="wide")

st.title("📊 会員データ・アップローダー")

# --- ファイルアップローダーの設置 ---
uploaded_file = st.file_uploader("会員データのCSVファイルを選択してください", type="csv")

if uploaded_file is not None:
    # アップロードされたファイルを読み込む
    df = pd.read_csv(uploaded_file)
    
    # データ処理（以前のロジックを適用）
    try:
        df['pre_reg_at'] = pd.to_datetime(df['pre_reg_at'])
        df['month'] = df['pre_reg_at'].dt.to_period('M').astype(str)

        # 月ごとの集計
        monthly_summary = df.groupby('month').size().reset_index(name='仮登録数')
        
        # 「通過」ステータスのカウント
        # ※実際のCSVの列名が 'status' であることを確認してください
        approved_df = df[df['status'] == '通過']
        approved_summary = approved_df.groupby('month').size().reset_index(name='本登録数')

        # 結合と累計計算
        final_df = pd.merge(monthly_summary, approved_summary, on='month', how='left').fillna(0)
        final_df['累計仮登録数'] = final_df['仮登録数'].cumsum()
        final_df['累計本登録数'] = final_df['本登録数'].cumsum()

        # --- ダッシュボード表示 ---
        st.success("データの読み込みに成功しました！")
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("総仮登録数", f"{final_df['仮登録数'].sum():,.0f} 人")
            st.plotly_chart(px.bar(final_df, x='month', y=['仮登録数', '本登録数'], barmode='group'), use_container_width=True)
        
        with c2:
            st.metric("総本登録数", f"{final_df['本登録数'].sum():,.0f} 人")
            st.plotly_chart(px.line(final_df, x='month', y=['累計仮登録数', '累計本登録数'], markers=True), use_container_width=True)

        with st.expander("データの中身を表示"):
            st.write(final_df)

    except Exception as e:
        st.error(f"エラーが発生しました。CSVの列名（pre_reg_at, status）を確認してください。詳細: {e}")

else:
    st.info("👆 上のボタンからCSVファイルをアップロードしてください。")
    st.markdown("""
    **必要なCSVの形式:**
    - `pre_reg_at`: 仮登録日時 (例: 2025-01-01)
    - `status`: 審査状況 (「通過」という文字列が含まれていること)
    """)
