import streamlit as st
from ortools.sat.python import cp_model

st.title("シフト自動作成アプリ🔥")

# ===== スタッフ設定 =====
staffs = [
    {"name": "社員A", "type": "社員", "register": True, "close": True},
    {"name": "社員B", "type": "社員", "register": True, "close": True},
    {"name": "パートA", "type": "パート", "register": True, "close": False},
    {"name": "バイトA", "type": "バイト", "register": True, "close": False},
    {"name": "バイトB", "type": "バイト", "register": False, "close": False},
    {"name": "バイトC", "type": "バイト", "register": True, "close": True},
]

days = ["月","火","水","木","金","土","日"]

# ===== 入力 =====
st.header("出勤希望（⭕️ / △ / ❌）")

availability = {}
for s in staffs:
    availability[s["name"]] = {}
    cols = st.columns(7)
    for i, d in enumerate(days):
        availability[s["name"]][d] = cols[i].selectbox(
            f"{s['name']}-{d}",
            ["❌","△","⭕️"],
            index=0
        )

# ===== ボタン =====
if st.button("シフト作成🔥"):

    model = cp_model.CpModel()

    shifts = ["早番","遅番"]

    # 必要人数
    need = {}
    for d in days:
        if d in ["土","日"]:
            need[(d,"早番")] = 4
            need[(d,"遅番")] = 4
        else:
            need[(d,"早番")] = 3
            need[(d,"遅番")] = 4

    # 変数
    work = {}
    for s in staffs:
        for d in days:
            for sh in shifts:
                work[(s["name"], d, sh)] = model.NewBoolVar(f"{s['name']}_{d}_{sh}")

    # ===== 制約 =====

    # 人数
    for d in days:
        for sh in shifts:
            model.Add(sum(work[(s["name"], d, sh)] for s in staffs) == need[(d,sh)])

    # ❌は入れない
    for s in staffs:
        for d in days:
            if availability[s["name"]][d] == "❌":
                for sh in shifts:
                    model.Add(work[(s["name"], d, sh)] == 0)

    # 社員は⭕️なら必ず入れる
    for s in staffs:
        if s["type"] == "社員":
            for d in days:
                if availability[s["name"]][d] == "⭕️":
                    model.Add(
                        sum(work[(s["name"], d, sh)] for sh in shifts) >= 1
                    )

    # パートは平日早番のみ
    for s in staffs:
        if s["type"] == "パート":
            for d in days:
                if d in ["土","日"]:
                    for sh in shifts:
                        model.Add(work[(s["name"], d, sh)] == 0)
                else:
                    model.Add(work[(s["name"], d, "遅番")] == 0)

    # レジ条件
    for d in days:
        # 早番
        model.Add(
            sum(work[(s["name"], d, "早番")] for s in staffs if s["register"]) >= 2
        )
        # 遅番
        model.Add(
            sum(work[(s["name"], d, "遅番")] for s in staffs if s["register"]) >= 2
        )
        model.Add(
            sum(work[(s["name"], d, "遅番")] for s in staffs if s["close"]) >= 1
        )

    # ===== 目的関数 =====
    objective_terms = []

    for s in staffs:
        for d in days:
            for sh in shifts:
                if availability[s["name"]][d] == "⭕️":
                    objective_terms.append(work[(s["name"], d, sh)] * 10)
                elif availability[s["name"]][d] == "△":
                    objective_terms.append(work[(s["name"], d, sh)] * 3)

    model.Maximize(sum(objective_terms))

    # ===== 解く =====
    solver = cp_model.CpSolver()
    result = solver.Solve(model)

    # ===== 出力 =====
    if result == cp_model.OPTIMAL or result == cp_model.FEASIBLE:
        st.success("完成🔥")

        for d in days:
            st.subheader(f"{d}")
            for sh in shifts:
                members = [
                    s["name"]
                    for s in staffs
                    if solver.Value(work[(s["name"], d, sh)]) == 1
                ]
                st.write(f"{sh}：{', '.join(members)}")
    else:
        st.error("シフト作れない（条件きつい）")
