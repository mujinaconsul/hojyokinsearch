import streamlit as st
import google.generativeai as genai

# --- 画面のUI設定 ---
st.set_page_config(page_title="補助金・助成金判定アプリ", page_icon="💰")
st.title("💰 補助金・助成金 簡易判定アプリ")
st.write("自社の状況や購入したいものを入力すると、AIが利用できそうな補助金・助成金の候補を提案します。")
st.warning("⚠️ 注意: AIの回答は推測を含む参考情報です。実際の応募にあたっては、必ず最新の公募要領を各省庁・自治体の公式サイトで確認するか、専門家にご相談ください。")

# --- 入力フォーム ---
st.header("📝 貴社の情報を入力してください")

# 単一入力（従業員数）
emp_count = st.number_input("従業員数（人）", min_value=0, value=5, step=1)

st.write("※以下の項目は、複数ある場合はカンマ（,）やスペースで区切って入力してください。")

# 複数入力可能項目（テキスト入力）
industry = st.text_input("業種・業界", placeholder="例：製造業, 飲食業, IT業")
location = st.text_input("事業所の所在地", placeholder="例：東京都港区, 大阪府大阪市")
items_to_buy = st.text_area("購入したいモノ・サービス", placeholder="例：顧客管理システム, 業務用オーブン, Webサイト制作")
budget = st.text_area("購入したいモノ・サービスの金額", placeholder="例：システム500万円, オーブン200万円")

# ボタンが押されたときの処理
if st.button("利用可能な補助金を判定する", type="primary"):
    if not industry or not location or not items_to_buy or not budget:
        st.warning("すべての項目に入力してください。")
    else:
        try:
            # SecretsからAPIキーを取得
            api_key = st.secrets["GOOGLE_API_KEY"]
            
            # AIの準備と実行
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            あなたは日本の中小企業診断士であり、補助金・助成金の専門家です。
            以下の企業情報と購入予定のモノ・サービスに基づいて、利用できる可能性のある最新の補助金や助成金（国や自治体のもの）を3〜5つ程度提案し、それぞれの要件にどのように当てはまっているかを解説してください。

            【企業情報】
            - 従業員数: {emp_count}人
            - 業種・業界: {industry}
            - 事業所の所在地: {location}

            【購入予定】
            - 購入したいモノ・サービス: {items_to_buy}
            - 金額: {budget}

            【出力形式の希望】
            各補助金について以下の構成で分かりやすく出力してください。
            1. **候補となる補助金・助成金の名称**
            2. **おすすめする理由**（入力された情報とどのようにマッチしているか）
            3. **要件を満たすための注意点やアドバイス**
            """
            
            # クルクル回るローディング表示
            with st.spinner("最新の補助金情報を分析・判定中です..."):
                response = model.generate_content(prompt)
            
            # 結果の表示
            st.success("✨ 判定が完了しました！")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"エラーが発生しました。設定を確認してください。（エラー詳細: {e}）")