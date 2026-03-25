import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# ページ設定
st.set_page_config(page_title="Fund KPI Dashboard", layout="wide")

# --- カスタムデザイン (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Serif JP', serif; }
    .stApp { background-color: #fdfcfb; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-top: 3px solid #c5a059;
        padding: 25px;
        border-radius: 4px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.02);
    }
    h1 { color: #2c2c2c; font-weight: 700; text-align: center; margin-bottom: 40px; }
    .stTabs [data-baseweb="tab"] { font-family: 'Noto Serif JP', serif; }
</style>
""", unsafe_allow_html=True)
st.title("📈 プラットフォーム総合KPIダッシュボード")

uploaded_file = st.file_uploader("月次集計データ（CSV）をアップロードしてください", type="csv")

if uploaded_file is not None:
    try:
        raw_bytes = uploaded_file.getvalue()
        try:
            decoded_text = raw_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            decoded_text = raw_bytes.decode('cp932')

        df = pd.read_csv(io.StringIO(decoded_text), sep=None, engine='python')
        df.columns = df.columns.str.strip()
        df['年月'] = df['年月'].astype(str)

        # 指標の計算
        df['仮登録CPA'] = df['総広告費'] / df['仮登録数']
        df['本登録CPA'] = df['総広告費'] / df['本登録数']
        df['平均投資回数'] = df['出資者数_延べ'] / df['出資者数_unique']
        df['リピート率(%)'] = (df['リピート数'] / df['出資者数_unique']) * 100
        df['アクティブ率(%)'] = (df['出資者数_unique'] / df['本登録数']) * 100
        df['上振率_運用開始(%)'] = (df['累計応募額_運用開始'] / df['累計運用額_運用開始']) * 100

        tab1, tab2, tab3, tab4 = st.tabs(["📢 獲得効率", "🤝 エンゲージメント", "💰 運用実績", "📄 データ一覧"])
        latest = df.iloc[-1]

        with tab1:
            st.subheader("マーケティング分析")
            m1, m2, m3 = st.columns(3)
            m1.metric("総広告費", f"¥{latest['総広告費']:,.0f}")
            m2.metric("本登録CPA", f"¥{latest['本登録CPA']:,.0f}")
            m3.metric("仮登録CPA", f"¥{latest['仮登録CPA']:,.0f}")
            
            fig_cpa = go.Figure()
            fig_cpa.add_trace(go.Bar(x=df['年月'], y=df['総広告費'], name='広告費', marker_color='#0052cc', opacity=0.7))
            fig_cpa.add_trace(go.Scatter(x=df['年月'], y=df['本登録CPA'], name='CPA', yaxis='y2', line=dict(color='#ff4b4b', width=3)))
            fig_cpa.update_layout(yaxis2=dict(overlaying='y', side='right'), template="plotly_white", hovermode="x unified")
            st.plotly_chart(fig_cpa, use_container_width=True)

        with tab2:
            st.subheader("投資家アクション")
            m1, m2, m3 = st.columns(3)
            m1.metric("リピート率", f"{latest['リピート率(%)']:.1f}%")
            m2.metric("アクティブ率", f"{latest['アクティブ率(%)']:.1f}%")
            m3.metric("平均投資回数", f"{latest['平均投資回数']:.2f}回")
            
            fig_eng = px.line(df, x='年月', y=['リピート率(%)', 'アクティブ率(%)'], markers=True, template="plotly_white")
            st.plotly_chart(fig_eng, use_container_width=True)

        with tab3:
            st.subheader("AUM推移")
            st.metric("現在のAUM", f"¥{latest['AUM']:,.0f}")
            fig_aum = px.area(df, x='年月', y='AUM', color_discrete_sequence=['#00b894'], template="plotly_white")
            st.plotly_chart(fig_aum, use_container_width=True)

        with tab4:
            st.dataframe(df)

    except Exception as e:
        st.error(f"読み込みエラー: {e}")
