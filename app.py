import streamlit as st
import google.generativeai as genai
import gdown
import os
import glob
import PyPDF2

# --- 画面のUI設定 ---
st.set_page_config(page_title="独自データAIアシスタント", page_icon="🍷")
st.title("🍷 独自データAIアシスタント (Googleドライブ連携)")
st.write("Googleドライブ内のPDFやテキストを読み込み、それを元にAIが回答を出力します。")

# --- 情報の取得と読み込み ---
@st.cache_data(ttl=3600) # 1時間ごとに再読み込みして最新化する設定
def load_drive_data():
    folder_url = "https://drive.google.com/drive/u/0/folders/1bLt7HvMpvE41k5IBZEylMHoGxH_UlsET"
    output_folder = "drive_data"
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        # gdownでフォルダごとダウンロード
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
                st.warning(f"PDFの読み込みに失敗しました ({filepath}): {e}")
        elif filepath.lower().endswith(".txt") or filepath.lower().endswith(".csv"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    all_text += f.read() + "\n"
            except Exception as e:
                pass
                
    if not all_text.strip():
        return "フォルダ内に読み込めるPDFやテキストデータが見つかりませんでした。ファイル形式を確認してください。"
    return all_text

# データ読み込みの実行
with st.spinner("Googleドライブからデータを読み込んでいます...（初回や更新時は少し時間がかかります）"):
    context_text = load_drive_data()

# --- 入力フォーム ---
st.header("📝 質問や指示を入力してください")
user_query = st.text_area("内容", placeholder="例：ワインエナジー様の現在の課題と、提案する商品戦略をまとめてください。")

# ボタンが押されたときの処理
if st.button("AIに回答させる", type="primary"):
    if not user_query:
        st.warning("質問や指示を入力してください。")
    elif "失敗しました" in context_text or "見つかりませんでした" in context_text:
        st.error(context_text)
        st.info("💡 フォルダの共有設定が「リンクを知っている全員」になっているか、また中にPDFやテキストファイルが入っているか確認してください。")
    else:
        try:
            # SecretsからAPIキーを取得（前回修正した名称に合わせています）
            api_key = st.secrets["GOOGLE_API_KEY"]
            
            # AIの準備と実行
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            あなたは優秀なコンサルタントAIです。
            以下の【参考資料】（Googleドライブから取得したデータ）を最優先の根拠として、ユーザーの【入力】に対して出力を行ってください。
            資料にない情報は推測で語らず、「資料に記載がありません」と答えてください。

            【参考資料】
            {context_text}

            【入力】
            {user_query}
            """
            
            with st.spinner("資料を分析して回答を作成中です..."):
                response = model.generate_content(prompt)
            
            # 結果の表示
            st.success("✨ 完了しました！")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"エラーが発生しました。（詳細: {e}）")
