import streamlit as st
import pandas as pd
import io
import plotly.express as px

# ページ設定
st.set_page_config(page_title="Fund Operations Dashboard", layout="wide")

st.title("📈 ファンド運営状況ダッシュボード")
st.markdown("CSVファイルをアップロードして、会員登録状況を可視化します。")

# --- 1. ファイルアップローダー ---
uploaded_file = st.file_uploader("会員データのCSVファイルを選択してください", type="csv")

if uploaded_file is not None:
    try:
        # 文字コードと区切り文字の自動判定ロジック
        raw_bytes = uploaded_file.getvalue()
        
        # 1. デコード試行 (UTF-8 -> Shift-JIS)
        try:
            decoded_text = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            decoded_text = raw_bytes.decode('cp932') # Excel標準のShift-JIS系

        # 2. Pandasで読み込み (sep=Noneでカンマ/タブを自動判別)
        df = pd.read_csv(
            io.StringIO(decoded_text),
            sep=None,
            engine='python',
            on_bad_lines='skip' # 行がずれている不正な行を飛ばす
        )

        # 読み込み成功時のプレビュー
        with st.expander("📥 アップロードされたデータの確認 (最初の5行)"):
            st.write(df.head())

        st.divider()

        # --- 2. 列名の選択 (ユーザーがCSVに合わせて指定) ---
        st.sidebar.header("🔍 列名の設定")
        st.sidebar.info("CSV内の正しい列名を選択してください")
        
        all_columns = df.columns.tolist()
        
        # 推測してデフォルト値をセットするロジック
        def find_default(keywords, cols):
            for k in keywords:
                for c in cols:
                    if k in str(c): return c
            return cols[0]

        date_col = st.sidebar.selectbox(
            "仮登録日時の列", 
            all_columns, 
            index=all_columns.index(find_default(["登録", "date", "at", "time"], all_columns))
        )
        
        status_col = st.sidebar.selectbox(
            "審査ステータスの列", 
            all_columns, 
            index=all_columns.index(find_default(["状態", "ステータス", "status", "審査"], all_columns))
        )

        # --- 3. データ加工ロジック ---
        # 日付型変換
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col]) # 日付が不正な行を除外
        
        # 月別ラベルの作成
        df['month'] = df[date_col].dt.to_period('M').astype(str)
        df = df.sort_values('month')

        # 集計
        # 1. 仮登録数 (全レコード)
        monthly_pre = df.groupby('month').size().reset_index(name='仮登録数')
        
        # 2. 本登録数 (ステータスが「通過」を含むもの)
        # ※「通過」という文字が含まれているか判定 (大文字小文字無視)
        approved_df = df[df[status_col].astype(str).str.contains("通過", na=False)]
        monthly_main = approved_df.groupby('month').size().reset_index(name='本登録数')

        # データの結合
        stats_df = pd.merge(monthly_pre, monthly_main, on='month', how='left').fillna(0)
        
        # 累計計算
        stats_df['累計仮登録数'] = stats_df['仮登録数'].cumsum()
        stats_df['累計本登録数'] = stats_df['本登録数'].cumsum()
        stats_df['本登録率(%)'] = (stats_df['本登録数'] / stats_df['仮登録数'] * 100).round(1)

        # --- 4. ダッシュボード表示 ---
        # KPIカード
        latest_total_pre = stats_df['累計仮登録数'].iloc[-1]
        latest_total_main = stats_df['累計本登録数'].iloc[-1]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("総仮登録数", f"{latest_total_pre:,.0f} 名")
        m2.metric("総本登録数", f"{latest_total_main:,.0f} 名")
        m3.metric("全体本登録率", f"{(latest_total_main/latest_total_pre*100):.1f} %")

        # グラフセクション
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig_bar = px.bar(
                stats_df, x='month', y=['仮登録数', '本登録数'],
                title="月次登録推移", barmode='group',
                color_discrete_map={"仮登録数": "#A0A0A0", "本登録数": "#00CC96"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            fig_line = px.line(
                stats_df, x='month', y=['累計仮登録数', '累計本登録数'],
                title="累計登録推移", markers=True,
                color_discrete_map={"累計仮登録数": "#A0A0A0", "累計本登録数": "#00CC96"}
            )
            st.plotly_chart(fig_line, use_container_width=True)

        st.subheader("月次詳細データ")
        st.dataframe(stats_df.sort_values('month', ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.info("ヒント: CSVの形式が正しいか、またはサイドバーで正しい列名を選択しているか確認してください。")

else:
    # ファイル未アップロード時の表示
    st.info("👆 左上のボタンから会員データのCSVをアップロードしてください。")
    st.image("https://via.placeholder.com/800x400.png?text=Waiting+for+CSV+Upload...", use_container_width=True)
