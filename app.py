import streamlit as st
import pandas as pd
from datetime import date, timedelta
from ortools.sat.python import cp_model

st.set_page_config(page_title="シフト管理 完全版", layout="wide")

# -------------------------
# 初期データ
# -------------------------
if "staffs" not in st.session_state:
    st.session_state.staffs = [
        {"name": "田中", "role": "店長", "can_register": True, "can_close": True},
        {"name": "佐藤", "role": "バイト", "can_register": True, "can_close": False},
        {"name": "鈴木", "role": "パート", "can_register": True, "can_close": False},
        {"name": "山本", "role": "社員", "can_register": True, "can_close": True},
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
    menu = st.sidebar.selectbox("メニュー", ["シフト入力", "スタッフ管理", "自動作成"])
else:
    menu = "シフト入力"

# -------------------------
# スタッフ管理
# -------------------------
if role == "店長" and menu == "スタッフ管理":
    st.title("スタッフ管理")

    name = st.text_input("名前")
    role_sel = st.selectbox("役割", ["バイト", "パート", "社員"])
    reg = st.checkbox("レジできる")
    close = st.checkbox("締めできる")

    if st.button("追加"):
        st.session_state.staffs.append({
            "name": name,
            "role": role_sel,
            "can_register": reg,
            "can_close": close
        })

    st.write(st.session_state.staffs)

# -------------------------
# シフト入力
# -------------------------
st.title("シフト入力")

start = st.date_input("開始日", date.today())
days = st.slider("日数", 7, 7, 7)
dates = [start + timedelta(days=i) for i in range(days)]

for d in dates:
    st.subheader(str(d))
    c1, c2 = st.columns(2)

    early = c1.selectbox("早番", ["⭕️","△","❌"], key=f"{user}_{d}_e")
    late  = c2.selectbox("遅番", ["⭕️","△","❌"], key=f"{user}_{d}_l")

    st.session_state.shift[(user,d,"e")] = early
    st.session_state.shift[(user,d,"l")] = late

# -------------------------
# 自動作成
# -------------------------
if role == "店長" and menu == "自動作成":

    if st.button("シフト自動生成🔥"):

        model = cp_model.CpModel()
        staff = st.session_state.staffs
        N = len(staff)
        D = len(dates)

        x = {}
        for i in range(N):
            for j in range(D):
                for sft in ["e","l"]:
                    x[i,j,sft] = model.NewBoolVar(f"x_{i}_{j}_{sft}")

        # 必要人数
        for j,d in enumerate(dates):
            if d.weekday()<5:
                e_need,l_need = 3,4
            else:
                e_need,l_need = 4,4

            model.Add(sum(x[i,j,"e"] for i in range(N))==e_need)
            model.Add(sum(x[i,j,"l"] for i in range(N))==l_need)

        # 制約
        for i,s in enumerate(staff):
            for j,d in enumerate(dates):
                e_req = st.session_state.shift.get((s["name"],d,"e"),"❌")
                l_req = st.session_state.shift.get((s["name"],d,"l"),"❌")

                if e_req=="❌":
                    model.Add(x[i,j,"e"]==0)
                if l_req=="❌":
                    model.Add(x[i,j,"l"]==0)

                # 社員⭕️強制
                if s["role"]=="社員":
                    if e_req=="⭕️": model.Add(x[i,j,"e"]==1)
                    if l_req=="⭕️": model.Add(x[i,j,"l"]==1)

                # パート平日早番⭕️強制
                if s["role"]=="パート" and d.weekday()<5:
                    if e_req=="⭕️": model.Add(x[i,j,"e"]==1)

        # レジ条件
        for j in range(D):
            model.Add(sum(x[i,j,"e"] for i,s in enumerate(staff) if s["can_register"])>=2)
            model.Add(sum(x[i,j,"l"] for i,s in enumerate(staff) if s["can_register"])>=2)

            model.Add(sum(x[i,j,"l"] for i,s in enumerate(staff) if s["can_close"])>=1)

        # 目的関数（⭕️優先）
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

        # 出力
        data=[]
        for j,d in enumerate(dates):
            for i,s in enumerate(staff):
                if solver.Value(x[i,j,"e"]):
                    data.append([d,"早番",s["name"]])
                if solver.Value(x[i,j,"l"]):
                    data.append([d,"遅番",s["name"]])

        df=pd.DataFrame(data,columns=["日付","シフト","名前"])
        st.dataframe(df)
