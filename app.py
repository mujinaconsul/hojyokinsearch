import streamlit as st
import google.generativeai as genai
import gdown
import os
import glob
import PyPDF2

# --- 画面のUI設定 ---
st.set_page_config(page_title="省力化投資補助金 判定アプリ", page_icon="🏢")
st.title("🏢 中小企業省力化投資補助金 簡易判定アプリ")
st.write("自社の状況や導入したい製品を入力すると、最新の公募要領や対象製品リスト（独自データ）に基づき、要件を満たす可能性があるかをAIが判定します。")
st.warning("⚠️ 注意: AIの回答は参考情報です。実際の申請にあたっては、必ず最新の公募要領をご確認いただくか、認定支援機関等の専門家にご相談ください。")

# --- Googleドライブからの情報取得 ---
@st.cache_data(ttl=3600) # 1時間ごとに再読み込み
def load_drive_data():
    # ご指定のGoogleドライブフォルダURL
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
        return "※現在、読み込める参考資料がフォルダにありません。"
    return all_text

# データ読み込みの実行
with st.spinner("最新の補助金・対象製品データを読み込んでいます..."):
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
            あなたは認定経営革新等支援機関として実務を行う、補助金の専門家AIです。
            ユーザーは「中小企業省力化投資補助金」の活用を検討している事業者です。
            以下の【企業情報】と【購入予定】、そして【参考資料】（Googleドライブから取得した最新の公募要領やカタログデータ等）に基づいて、
            この事業者が同補助金の要件に当てはまる可能性がどの程度あるか判定してください。

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
            1. 必ず【参考資料】の情報を最優先の判断基準としてください。省力化投資補助金は「カタログ登録されている製品」であることが重要である等の特有の要件を踏まえて判定してください。
            2. 出力は以下の2項目のみとし、指定された形式を厳密に守ってください。挨拶やまとめの言葉は不要です。

            1. 判定
            ※以下の3つのうちから、最も適切なものを1つだけそのまま出力してください。
            ・対象の可能性あり
            ・一部対象の可能性あり
            ・対象の可能性が低い

            2. 判定のポイント
            ※なぜその判定になったのか、【企業情報】や【購入予定】と【参考資料】の要件を照らし合わせて、事業者向けにわかりやすく解説してください。カタログ登録製品の確認など、注意すべき懸念点があればそれも含めてください。
            """
            
            with st.spinner("要件と照らし合わせて判定しています..."):
                response = model.generate_content(prompt)
            
            # 結果の表示
            st.success("✨ 判定が完了しました！")
            st.markdown(response.text)
            
        except KeyError:
             st.error("APIキーが設定されていません。StreamlitのSecrets設定を確認してください。")
        except Exception as e:
            st.error(f"エラーが発生しました。（詳細: {e}）")
