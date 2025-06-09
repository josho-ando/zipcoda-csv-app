import streamlit as st
import pandas as pd
import requests
import io
import chardet
from time import sleep

st.title("CSV住所データに郵便番号を付与するアプリ")

# -------------------------------------
# 郵便番号取得関数（ZIPCODA API利用）
# -------------------------------------
def get_zipcode(address):
    try:
        response = requests.get("https://zipcoda.net/api", params={"address": address})
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [{}])[0].get("zipcode", "該当なし")
        else:
            return "APIエラー"
    except Exception:
        return "取得失敗"

# -------------------------------------
# エンコーディング判定
# -------------------------------------
def detect_encoding(file):
    raw = file.read()
    result = chardet.detect(raw)
    encoding = result['encoding']
    return encoding, io.BytesIO(raw)  # 元データを戻す（再利用のため）

# -------------------------------------
# メイン処理
# -------------------------------------
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    encoding, bytes_io = detect_encoding(uploaded_file)
    st.write(f"検出された文字コード: `{encoding}`")

    try:
        df = pd.read_csv(bytes_io, encoding=encoding)
    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
        st.stop()

    st.success("CSVファイルを正常に読み込みました。")

    # 住所列の選択
    address_column = st.selectbox("住所が含まれる列を選んでください", df.columns)

    if st.button("郵便番号を付与する"):
        with st.spinner("郵便番号を取得中..."):
            zipcodes = []
            for address in df[address_column]:
                zip_code = get_zipcode(str(address))
                zipcodes.append(zip_code)
                sleep(0.1)  # APIサーバーへの負荷軽減

            df["郵便番号"] = zipcodes
        st.success("郵便番号の付与が完了しました。")

        st.dataframe(df)

        # 出力ファイル作成（UTF-8）
        csv_utf8 = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 郵便番号付きCSVをダウンロード（UTF-8）",
            data=csv_utf8,
            file_name="output_with_zipcode_utf8.csv",
            mime="text/csv",
        )

        # 出力ファイル作成（Shift-JIS）
        csv_sjis = df.to_csv(index=False).encode("cp932", errors="ignore")
        st.download_button(
            label="📥 郵便番号付きCSVをダウンロード（Shift-JIS）",
            data=csv_sjis,
            file_name="output_with_zipcode_sjis.csv",
            mime="text/csv",
        )
