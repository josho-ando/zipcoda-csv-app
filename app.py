import streamlit as st
import pandas as pd
import requests
import chardet
import io
import re

# 番地まで抽出する関数（漢字 & ハイフン形式対応）
def extract_up_to_banchi(address):
    pattern1 = r'\d{1,5}[-－]\d{1,5}([-－]\d{1,5})?'
    pattern2 = r'\d{1,5}丁目\d{1,5}番地(\d{1,5}号)?'
    pattern3 = r'\d{1,5}丁目\d{1,5}番(\d{1,5}号)?'
    for pattern in [pattern2, pattern3, pattern1]:
        match = re.search(pattern, address)
        if match:
            end = match.end()
            return address[:end]
    return address

# 郵便番号取得関数（Zipcoda API）
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

# CSVの文字コードを自動判別して読み込む
def load_csv(file):
    raw = file.read()

    # UTF-8-SIG（Excelなど）で試行
    try:
        return pd.read_csv(io.BytesIO(raw), encoding='utf-8-sig')
    except Exception:
        pass

    # Shift_JIS（CP932）で試行
    try:
        return pd.read_csv(io.BytesIO(raw), encoding='cp932')
    except Exception:
        pass

    # chardetで自動判定
    encoding = chardet.detect(raw)['encoding']
    try:
        return pd.read_csv(io.BytesIO(raw), encoding=encoding)
    except Exception:
        st.error("CSVの読み込みに失敗しました。文字コードが不正か、破損している可能性があります。")
        return pd.DataFrame()

# def load_csv(filelike):
#     raw = filelike.read()

#     # まず UTF-8-SIG で試す（Excelで保存されたCSVに多い）
#     try:
#         return pd.read_csv(io.BytesIO(raw), encoding='utf-8-sig')
#     except Exception:
#         pass

#     # 次に Shift_JIS（cp932）で試す
#     try:
#         return pd.read_csv(io.BytesIO(raw), encoding='cp932')
#     except Exception:
#         pass

#     # それでも無理なら chardet で推定
#     encoding = chardet.detect(raw)['encoding']
#     try:
#         return pd.read_csv(io.BytesIO(raw), encoding=encoding)
#     except Exception:
#         st.error("CSVの読み込みに失敗しました。文字コードが不正か、破損している可能性があります。")
#         return pd.DataFrame()

# Streamlit UI
st.title("住所→郵便番号 変換アプリ（Zipcoda連携）")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])
if uploaded_file is not None:
    # .read() は1回だけ
    raw_data = uploaded_file.read()
    df = load_csv(io.BytesIO(raw_data))

    address_col = st.number_input("住所が含まれる列番号を指定（1から）", min_value=1, max_value=len(df.columns), value=1)

    if st.button("郵便番号を付与する"):
        addresses = df.iloc[:, address_col - 1].astype(str)
        cleaned_addresses = addresses.map(extract_up_to_banchi)

        st.write("抽出された番地までの住所（デバッグ表示）", cleaned_addresses.head(10))

        zipcodes = cleaned_addresses.map(get_zipcode)
        df['郵便番号'] = zipcodes

        
        st.success("処理完了！結果を以下に表示します。")
        st.dataframe(df)

        # ダウンロードリンク
        csv_out = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="変換済みCSVをダウンロード",
            data=csv_out,
            file_name='converted_with_zipcodes.csv',
            mime='text/csv'
        )
