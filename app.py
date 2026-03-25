import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

st.set_page_config(page_title="Fund KPI Dashboard", layout="wide")
st.title("📊 プラットフォーム総合KPIダッシュボード")

uploaded_file = st.file_uploader("月次集計データ（CSV）をアップロードしてください", type="csv")

if uploaded_file is not None:
    try:
        # 文字コードの自動判定読み込み
        raw_bytes = uploaded_file.getvalue()
        try:
        　　# ★修正1：Excel特有の「BOM付きUTF-8」に対応するため'utf-8-sig' に変更
            decoded_text = raw_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            decoded_text = raw_bytes.decode('cp932')

        df = pd.read_csv(io.StringIO(decoded_text), sep=None, engine='python')
        # ★修正2：列名の前後にある「見えない空白や改行」を強制的に削除
        df.columns =df.columns.str.strip()
    
        df['年月'] = df['年月'].astype(str) # X軸用に文字列化

        # --- 足りない指標の自動計算（CSVにあれば上書き、なければ計算） ---
        # 1. マーケティング指標
        df['仮登録CPA'] = df['総広告費'] / df['仮登録数']
        df['本登録CPA'] = df['総広告費'] / df['本登録数']
        
        # 2. エンゲージメント指標
        df['平均投資回数'] = df['出資者数_延べ'] / df['出資者数_unique']
        df['リピート率(%)'] = (df['リピート数'] / df['出資者数_unique']) * 100
        df['アクティブ率(%)'] = (df['出資者数_unique'] / df['本登録数']) * 100
        
        # 3. ファンド実績指標
        df['上振率_運用開始(%)'] = (df['累計応募額_運用開始'] / df['累計運用額_運用開始']) * 100
        df['上振率_募集開始(%)'] = (df['累計応募額_募集開始'] / df['累計運用額_募集開始']) * 100

        # --- タブの作成 ---
        tab1, tab2, tab3, tab4 = st.tabs(["📢 マーケティング", "🤝 顧客エンゲージメント", "💰 ファンド実績", "📄 生データ確認"])

        # 最新月のデータ取得
        latest = df.iloc[-1]

        # ==========================================
        # TAB 1: マーケティング・獲得効率
        # ==========================================
        with tab1:
            st.subheader("マーケティングKPI")
            c1, c2, c3 = st.columns(3)
            c1.metric("当月 総広告費", f"¥{latest['総広告費']:,.0f}")
            c2.metric("当月 本登録CPA", f"¥{latest['本登録CPA']:,.0f}")
            c3.metric("当月 仮登録CPA", f"¥{latest['仮登録CPA']:,.0f}")

            fig_cpa = go.Figure()
            fig_cpa.add_trace(go.Bar(x=df['年月'], y=df['総広告費'], name='総広告費', yaxis='y1', opacity=0.6))
            fig_cpa.add_trace(go.Scatter(x=df['年月'], y=df['本登録CPA'], name='本登録CPA', mode='lines+markers', yaxis='y2', line=dict(color='red')))
            fig_cpa.update_layout(
                title="広告費とCPAの推移",
                yaxis=dict(title="広告費 (円)"),
                yaxis2=dict(title="CPA (円)", overlaying='y', side='right'),
                barmode='group'
            )
            st.plotly_chart(fig_cpa, use_container_width=True)

        # ==========================================
        # TAB 2: 顧客エンゲージメント・LTV
        # ==========================================
        with tab2:
            st.subheader("アクティブ・リピート分析")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("アクティブ率", f"{latest['アクティブ率(%)']:.1f}%")
            c2.metric("リピート率", f"{latest['リピート率(%)']:.1f}%")
            c3.metric("出資単価 (unique)", f"¥{latest['出資単価_unique']:,.0f}")
            c4.metric("平均投資回数", f"{latest['平均投資回数']:.2f} 回")

            col_eng1, col_eng2 = st.columns(2)
            with col_eng1:
                fig_investors = px.bar(df, x='年月', y=['出資者数_unique', '出資者数_延べ'], barmode='group', title="出資者数の推移 (Unique vs 延べ)")
                st.plotly_chart(fig_investors, use_container_width=True)
            with col_eng2:
                fig_rates = px.line(df, x='年月', y=['アクティブ率(%)', 'リピート率(%)'], markers=True, title="エンゲージメント率の推移")
                st.plotly_chart(fig_rates, use_container_width=True)

        # ==========================================
        # TAB 3: ファンド運用・財務パフォーマンス
        # ==========================================
        with tab3:
            st.subheader("AUM・運用実績")
            c1, c2, c3 = st.columns(3)
            c1.metric("現在のAUM", f"¥{latest['AUM']:,.0f}")
            c2.metric("累計運用額 (運用開始)", f"¥{latest['累計運用額_運用開始']:,.0f}")
            c3.metric("累計配当額", f"¥{latest['累計配当額']:,.0f}")

            col_fund1, col_fund2 = st.columns(2)
            with col_fund1:
                fig_aum = px.area(df, x='年月', y='AUM', title="AUM (運用資産残高) の推移", color_discrete_sequence=['#00CC96'])
                st.plotly_chart(fig_aum, use_container_width=True)
            with col_fund2:
                fig_upside = px.line(df, x='年月', y=['上振率_運用開始(%)', '上振率_募集開始(%)'], markers=True, title="募集時の上振率の推移")
                st.plotly_chart(fig_upside, use_container_width=True)

        # ==========================================
        # TAB 4: 生データ確認
        # ==========================================
        with tab4:
            st.dataframe(df, use_container_width=True)

    except KeyError as e:
        st.error(f"エラー：CSVに以下の列が見つかりません。列名を確認してください。 -> {e}")
        st.info("必須の列名: 年月, 総広告費, 仮登録数, 本登録数, 出資者数_unique, 出資者数_延べ, 出資単価_unique, 出資単価_延べ, リピート数, AUM, 累計運用額_運用開始, 累計運用額_募集開始, 累計応募額_運用開始, 累計応募額_募集開始, 累計配当額")
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")

else:
    st.info("👆 ファイルアップローダーから、月次集計データ(CSV)を選択してください。")
