import streamlit as st
import google.generativeai as genai
import gdown
import os
import glob
import PyPDF2

# --- 画面のUI設定 ---
st.set_page_config(page_title="補助金・助成金判定アプリ", page_icon="💰")
st.title("💰 補助金・助成金 簡易判定アプリ")
st.write("自社の状況や購入したいものを入力すると、AIが最新の資料データを元に、利用できそうな補助金・助成金の候補と要件の合致度を判定します。")
st.warning("⚠️ 注意: AIの回答は推測を含む参考情報です。実際の応募にあたっては、必ず最新の公募要領を各省庁・自治体の公式サイトで確認するか、専門家にご相談ください。")

# --- Googleドライブからの情報取得 ---
@st.cache_data(ttl=3600) # 1時間ごとに再読み込み
def load_drive_data():
    folder_url = "https://drive.google.com/drive/u/0/folders/1bLt7HvMpvE41k5IBZEylMHoGxH_UlsET"
    output_folder = "drive_data"
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        # gdownでフォルダをダウンロード
        gdown.download_folder(folder_url, output=output_folder, quiet=False, use_cookies=False)
    except Exception as e:
        return f"フォルダのダウンロードに失敗しました: {e}"

    all_text = ""
    # フォルダ内のPDFとテキストを読み込む
    for filepath in glob.glob(f"{output_folder}/*"):
        if filepath.lower().endswith(".pdf"):
            try:
                reader = PyPDF2.PdfReader(filepath)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
            except Exception as e:
                pass
        elif filepath.lower().endswith(".txt") or filepath.lower().endswith(".csv"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    all_text += f.read() + "\n"
            except Exception as e:
                pass
                
    if not all_text.strip():
        return "※現在、読み込める参考資料（PDFやテキスト）がフォルダにありません。一般的な最新情報のみで回答します。"
    return all_text

# データ読み込みの実行
with st.spinner("最新の補助金データを読み込んでいます..."):
    context_text = load_drive_data()

# --- 入力フォーム ---
st.header("📝 貴社の情報を入力してください")

# 単一入力（従業員数）
emp_count = st.number_input("従業員数（人）", min_value=0, value=5, step=1)

st.write("※以下の項目は、複数ある場合はカンマ（,）やスペース、改行で区切って入力してください。")

# 複数入力可能項目
industry = st.text_input("業種・業界", placeholder="例：製造業, 飲食業, IT業")
location = st.text_input("事業所の所在地", placeholder="例：東京都港区, 大阪府大阪市")
items_to_buy = st.text_area("購入したいモノ・サービス", placeholder="例：顧客管理システム, 業務用オーブン, Webサイト制作")
budget = st.text_area("購入したいモノ・サービスの合計金額", placeholder="例：システム500万円, オーブン200万円")

# ボタンが押されたときの処理
if st.button("利用可能な補助金を判定する", type="primary"):
    if not industry or not location or not items_to_buy or not budget:
        st.warning("すべての項目に入力してください。")
    else:
        try:
            # Secretsから安全にAPIキーを取得
            api_key = st.secrets["GOOGLE_API_KEY"]
            
            # AIの準備と実行
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # AIへの指示（プロンプト）
            prompt = f"""
            あなたは日本の補助金・助成金の専門家です。
            以下の【企業情報】と【購入予定】、そして【参考資料】（最新の公募要領やガイドラインのデータ）に基づいて、
            事業者が「自社で利用できるか」を自分で判断できるように、利用可能な補助金や助成金を提案してください。

            【企業情報】
            - 従業員数: {emp_count}人
            - 業種・業界: {industry}
            - 事業所の所在地: {location}

            【購入予定】
            - 購入したいモノ・サービス: {items_to_buy}
            - 金額: {budget}

            【参考資料（Googleドライブ内のデータ）】
            {context_text}
            
            【出力のルール】
            1. 【参考資料】の情報を中心に根拠とし、資料にない不足部分は一般的な最新情報で補って回答してください。
            2. 各補助金について、以下の構成で出力してください。
               - 補助金の名称
               - なぜこの要件に当てはまるのか（適合理由）
               - 想定される補助額・補助率の目安
               - 申請に向けた今後の具体的なステップや注意点
            """
            
            with st.spinner("情報を分析し、最適な補助金を判定しています..."):
                response = model.generate_content(prompt)
            
            # 結果の表示
            st.success("✨ 判定が完了しました！")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"エラーが発生しました。（詳細: {e}）")
            st.info("APIキーの設定や、requirements.txtの記述が正しいか確認してください。")
