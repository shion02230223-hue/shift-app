import streamlit as st
import pandas as pd
from datetime import date, timedelta
from ortools.sat.python import cp_model

st.set_page_config(page_title="シフト管理", layout="wide")

# -------------------------
# CSS（おしゃれ化🔥）
# -------------------------
st.markdown("""
<style>
.main {
    background-color: #f7f7f7;
}
.block-container {
    padding: 2rem;
}
.card {
    background: white;
    padding: 15px;
    border-radius: 15px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    margin-bottom: 15px;
}
.shift-btn button {
    width: 100%;
    border-radius: 10px;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# 初期データ
# -------------------------
if "staffs" not in st.session_state:
    st.session_state.staffs = [
        {"name": "田中", "role": "店長", "can_register": True, "can_close": True},
        {"name": "佐藤", "role": "バイト", "can_register": True, "can_close": False},
        {"name": "鈴木", "role": "パート", "can_register": True, "can_close": False},
    ]

if "shift" not in st.session_state:
    st.session_state.shift = {}

# -------------------------
# ログイン
# -------------------------
st.sidebar.title("ログイン")
names = [s["name"] for s in st.session_state.staffs]
user = st.sidebar.selectbox("名前", names)
me = next(s for s in st.session_state.staffs if s["name"] == user)
role = me["role"]

# -------------------------
# メニュー
# -------------------------
if role == "店長":
    menu = st.sidebar.radio("メニュー", ["シフト入力", "メンバー管理", "自動作成"])
else:
    menu = "シフト入力"

# -------------------------
# メンバー管理
# -------------------------
if role == "店長" and menu == "メンバー管理":
    st.title("👥 メンバー管理")

    for i, s in enumerate(st.session_state.staffs):
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.subheader(s["name"])

            role_new = st.selectbox(
                "役割",
                ["店長","社員","パート","バイト"],
                index=["店長","社員","パート","バイト"].index(s["role"]),
                key=f"role_{i}"
            )

            col1, col2 = st.columns(2)
            reg = col1.checkbox("レジ可", value=s["can_register"], key=f"reg_{i}")
            close = col2.checkbox("締め可", value=s["can_close"], key=f"close_{i}")

            st.session_state.staffs[i]["role"] = role_new
            st.session_state.staffs[i]["can_register"] = reg
            st.session_state.staffs[i]["can_close"] = close

            st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    st.subheader("➕ メンバー追加")
    name = st.text_input("名前")
    role_new = st.selectbox("役割", ["バイト","パート","社員"])

    if st.button("追加"):
        st.session_state.staffs.append({
            "name": name,
            "role": role_new,
            "can_register": False,
            "can_close": False
        })
        st.success("追加完了！")

# -------------------------
# ⭕️△❌ボタン
# -------------------------
def select_shift(key):
    if key not in st.session_state:
        st.session_state[key] = "未"

    col1, col2, col3 = st.columns(3)

    if col1.button("⭕️", key=key+"_ok"):
        st.session_state[key] = "⭕️"
    if col2.button("△", key=key+"_maybe"):
        st.session_state[key] = "△"
    if col3.button("❌", key=key+"_no"):
        st.session_state[key] = "❌"

    return st.session_state[key]

# -------------------------
# シフト入力
# -------------------------
if menu == "シフト入力":

    st.title("📝 シフト入力")

    start = st.date_input("開始日", date.today())
    days = 7

    weekday = ["月","火","水","木","金","土","日"]
    dates = [start + timedelta(days=i) for i in range(days)]

    for d in dates:
        wd = weekday[d.weekday()]

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader(f"{d}（{wd}）")

        c1, c2 = st.columns(2)

        with c1:
            st.write("🌅 早番")
            early = select_shift(f"{user}_{d}_e")

        with c2:
            st.write("🌙 遅番")
            late = select_shift(f"{user}_{d}_l")

        st.session_state.shift[(user,d,"e")] = early
        st.session_state.shift[(user,d,"l")] = late

        st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 自動作成
# -------------------------
if role == "店長" and menu == "自動作成":

    st.title("🤖 シフト自動作成")

    if st.button("シフト生成🔥"):

        model = cp_model.CpModel()
        staff = st.session_state.staffs
        N = len(staff)

        weekday = ["月","火","水","木","金","土","日"]
        start = date.today()
        dates = [start + timedelta(days=i) for i in range(7)]

        x = {}
        for i in range(N):
            for j in range(7):
                for sft in ["e","l"]:
                    x[i,j,sft] = model.NewBoolVar(f"x_{i}_{j}_{sft}")

        for j,d in enumerate(dates):
            if d.weekday()<5:
                e_need,l_need = 3,4
            else:
                e_need,l_need = 4,4

            model.Add(sum(x[i,j,"e"] for i in range(N))==e_need)
            model.Add(sum(x[i,j,"l"] for i in range(N))==l_need)

        for i,s in enumerate(staff):
            for j,d in enumerate(dates):
                e_req = st.session_state.shift.get((s["name"],d,"e"),"❌")
                l_req = st.session_state.shift.get((s["name"],d,"l"),"❌")

                if e_req=="❌": model.Add(x[i,j,"e"]==0)
                if l_req=="❌": model.Add(x[i,j,"l"]==0)

                if s["role"]=="社員":
                    if e_req=="⭕️": model.Add(x[i,j,"e"]==1)
                    if l_req=="⭕️": model.Add(x[i,j,"l"]==1)

                if s["role"]=="パート" and d.weekday()<5:
                    if e_req=="⭕️": model.Add(x[i,j,"e"]==1)

        for j in range(7):
            model.Add(sum(x[i,j,"e"] for i,s in enumerate(staff) if s["can_register"])>=2)
            model.Add(sum(x[i,j,"l"] for i,s in enumerate(staff) if s["can_register"])>=2)
            model.Add(sum(x[i,j,"l"] for i,s in enumerate(staff) if s["can_close"])>=1)

        obj=[]
        for i,s in enumerate(staff):
            for j,d in enumerate(dates):
                e_req = st.session_state.shift.get((s["name"],d,"e"),"❌")
                l_req = st.session_state.shift.get((s["name"],d,"l"),"❌")

                if e_req=="⭕️": obj.append(10*x[i,j,"e"])
                elif e_req=="△": obj.append(3*x[i,j,"e"])

                if l_req=="⭕️": obj.append(10*x[i,j,"l"])
                elif l_req=="△": obj.append(3*x[i,j,"l"])

        model.Maximize(sum(obj))

        solver = cp_model.CpSolver()
        solver.Solve(model)

        data=[]
        for j,d in enumerate(dates):
            for i,s in enumerate(staff):
                if solver.Value(x[i,j,"e"]):
                    data.append([f"{d}（{weekday[d.weekday()]}）","早番",s["name"]])
                if solver.Value(x[i,j,"l"]):
                    data.append([f"{d}（{weekday[d.weekday()]}）","遅番",s["name"]])

        df=pd.DataFrame(data,columns=["日付","シフト","名前"])

        st.success("完成✨")
        st.dataframe(df)
