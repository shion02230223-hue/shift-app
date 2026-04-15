import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- ページ設定 ---
st.set_page_config(page_title="シフト管理アプリ", layout="wide")

# --- 初期データ ---
if "staffs" not in st.session_state:
    st.session_state.staffs = ["田中", "佐藤"]

# --- サイドメニュー ---
menu = st.sidebar.selectbox(
    "メニュー",
    ["🏠 ホーム", "📝 シフト作成", "👥 スタッフ管理"]
)

# ======================
# 🏠 ホーム
# ======================
if menu == "🏠 ホーム":
    st.title("📅 シフト管理アプリ")
    st.write("左のメニューから選択してください")

# ======================
# 👥 スタッフ管理（店長用）
# ======================
elif menu == "👥 スタッフ管理":
    st.title("👥 スタッフ管理")

    # 追加
    new_staff = st.text_input("スタッフ名を追加")
    if st.button("追加"):
        if new_staff:
            st.session_state.staffs.append(new_staff)
            st.success(f"{new_staff} を追加しました")

    # 一覧
    st.subheader("現在のスタッフ")
    st.write(st.session_state.staffs)

    # 削除
    delete_staff = st.selectbox("削除するスタッフ", st.session_state.staffs)
    if st.button("削除"):
        st.session_state.staffs.remove(delete_staff)
        st.warning(f"{delete_staff} を削除しました")

# ======================
# 📝 シフト作成
# ======================
elif menu == "📝 シフト作成":
    st.title("📝 シフト作成")

    # 日付
    start_date = st.date_input("開始日", date.today())
    days = st.slider("日数", 1, 14, 7)

    dates = [start_date + timedelta(days=i) for i in range(days)]

    shift_data = {}

    for name in st.session_state.staffs:
        st.markdown(f"### {name}")
        shift_data[name] = []
        for d in dates:
            choice = st.selectbox(
                f"{d}",
                ["⭕️", "△", "❌"],
                key=f"{name}_{d}"
            )
            shift_data[name].append(choice)

    df = pd.DataFrame(shift_data, index=dates)

    # 個人表示
    st.subheader("個人シフト")
    selected = st.selectbox("名前を選択", st.session_state.staffs)
    st.write(df[selected])

    # 全体
    if st.button("全体表示"):
        st.dataframe(df)
