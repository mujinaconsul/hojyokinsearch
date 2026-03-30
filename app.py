import streamlit as st
import google.generativeai as genai
import gdown
import os
import glob
import PyPDF2

# --- 画面のUI設定 ---
st.set_page_config(page_title="省力化投資補助金 判定アプリ", page_icon="🏢")
st.title("🏢 中小企業省力化投資補助金 簡易判定アプリ")
st.write("自社の状況や導入したい製品を入力すると、最新の公募要領や対象製品リストに基づき、要件を満たす可能性があるかを判定します。")
st.warning("⚠️ 注意: 判定結果は参考情報です。実際の申請にあたっては、必ず最新の公募要領をご確認いただくか、専門家にご相談ください。")

# --- Googleドライブからの情報取得 ---
@st.cache_data(ttl=3600) # 1時間ごとに再読み込み
def load_drive_data():
    folder_url = "https://drive.google.com/drive/u/0/folders/1bLt7HvMpvE41k5IBZEylMHoGxH_UlsET"
    output_folder = "drive_data"
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        gdown.download_folder(folder_url, output=output_folder, quiet=False, use_cookies=False)
    except Exception as e:
        return f"フォルダのダウンロードに失敗しました: {e}"

    all_text = ""
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
        return "※現在、読み込める参考資料がフォルダにありません。"
    return all_text

# データ読み込みの実行
with st.spinner("最新のデータを読み込んでいます..."):
    context_text = load_drive_data()

# --- 入力フォーム ---
st.header("📝 貴社の情報を入力してください")

# 単一入力（従業員数）
emp_count = st.number_input("従業員数（人）", min_value=0, value=5, step=1)

st.write("※以下の項目は、複数ある場合はカンマ（,）や改行で区切って入力してください。")

# 複数入力可能項目
industry = st.text_input("業種・業界", placeholder="例：製造業, 飲食業, 宿泊業")
location = st.text_input("事業所の所在地", placeholder="例：埼玉県戸田市, 東京都港区")
items_to_buy = st.text_area("購入（導入）したいモノ・サービス", placeholder="例：スチームコンベクションオーブン, 配膳ロボット, 券売機")
budget = st.text_area("購入したいモノ・サービスの合計金額", placeholder="例：オーブン200万円, ロボット150万円")

# ボタンが押されたときの処理
if st.button("補助金の要件にあてはまるか判定する", type="primary"):
    if not industry or not location or not items_to_buy or not budget:
        st.warning("すべての項目に入力してください。")
    else:
        try:
            # SecretsからAPIキーを取得
            api_key = st.secrets["GOOGLE_API_KEY"]
            
            # AIの準備と実行
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # AIへの指示（プロンプト）
            prompt = f"""
            あなたは補助金の専門家AIです。ユーザーは「中小企業省力化投資補助金」の活用を検討している事業者です。
            以下の【企業情報】と【購入予定】、および【参考資料】に基づいて、要件に当てはまる可能性を判定してください。

            【企業情報】
            - 従業員数: {emp_count}人
            - 業種・業界: {industry}
            - 事業所の所在地: {location}

            【購入予定】
            - 購入したいモノ・サービス: {items_to_buy}
            - 金額: {budget}

            【参考資料】
            {context_text}
            
            【出力のルール】
            1. 読み手は事業者自身です。「貴社」という言葉を使い、丁寧で分かりやすい文章にしてください。
            2. 出力は以下の2項目のみとし、指定された形式を厳密に守ってください。挨拶などは一切不要です。

            1. 判定
            ※以下の3つのうちから、最も適切なものを1つだけそのまま出力してください。
            ・対象の可能性あり
            ・一部対象の可能性あり
            ・対象の可能性が低い

            2. 判定のポイント
            ※なぜその判定になったのか、事業者向けに解説してください。
            ※【重要】必ず100文字以内で簡潔にまとめてください。
            """
            
            with st.spinner("要件と照らし合わせて判定しています..."):
                response = model.generate_content(prompt)
                result_text = response.text
            
            # 結果の表示
            st.success("✨ 判定が完了しました！")
            st.markdown(result_text)
            
            # --- 問い合わせ誘導メッセージの表示条件 ---
            # AIの出力から「1. 判定」の部分を抽出し、「対象の可能性あり」が選ばれたかチェックする
            first_part = result_text.split("2. 判定のポイント")[0]
            if "一部対象の可能性あり" not in first_part and "対象の可能性あり" in first_part:
                st.info("💡 **【おすすめ】対象となる可能性が高いようです！**\n\n具体的な申請手続きや、導入予定の製品がカタログに登録されているかの確認など、ぜひ当事務所（認定経営革新等支援機関）までお気軽にお問い合わせください。")
            
        except KeyError:
             st.error("APIキーが設定されていません。StreamlitのSecrets設定を確認してください。")
        except Exception as e:
            st.error(f"エラーが発生しました。（詳細: {e}）")
