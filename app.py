import streamlit as st
import pandas as pd
import json
import os

DATA_FILE = "building_data.json"

# 1. 資料處理核心 (預設資料已改為 V)
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "原料": {
                "H型鋼": [
                    {"規格": "V200x100x5.5x8", "單位重": "21.3", "截面積": "27.16"},
                    {"規格": "V400x200x8x13", "單位重": "66.0", "截面積": "84.12"}
                ]
            },
            "物料": {}, "消耗品": {}
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 初始化狀態
if 'db' not in st.session_state: st.session_state.db = load_data()
if 'main_cat' not in st.session_state: st.session_state.main_cat = None
if 'sub_cat' not in st.session_state: st.session_state.sub_cat = None
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# 控制編輯狀態與新增選單狀態
if 'edit_m' not in st.session_state: st.session_state.edit_m = False
if 'edit_s' not in st.session_state: st.session_state.edit_s = False
if 'show_add_menu' not in st.session_state: st.session_state.show_add_menu = False
if 'add_target' not in st.session_state: st.session_state.add_target = None

st.set_page_config(page_title="建築原物料查詢系統", layout="wide")

# 2. CSS 樣式修正
st.markdown("""
<style>
header { display: none !important; }
html, body, p, div, span, h1, h2, h3, h4, h5, h6, table, th, td, input, select, textarea, button {
    font-family: '華康中特圓體', 'Microsoft JhengHei', sans-serif !important;
    font-weight: normal !important;
}
/* 保護系統圖示 */
[data-testid="stIconMaterial"] { font-family: "Material Symbols Rounded" !important; }

/* 點選後的按鈕視覺效果 */
div[data-testid="stButton"] button[kind="primary"] {
    transform: scale(0.85) !important; opacity: 0.4 !important; transition: all 0.3s ease !important;
}

/* ===== 明細外框與表格框線加強 ===== */
[data-testid="column"]:nth-of-type(3) {
    border: 3px solid currentColor !important;
    border-radius: 12px;
    padding: 20px;
    min-height: 85vh;
    background-color: rgba(128, 128, 128, 0.05) !important; 
}

[data-testid="stTable"] table { 
    width: 100% !important; 
    table-layout: fixed !important; 
    border-collapse: collapse !important; 
    border: 2px solid currentColor !important;
}
[data-testid="stTable"] th, [data-testid="stTable"] td { 
    border: 1px solid currentColor !important; 
}
[data-testid="stTable"] thead th {
    border-bottom: 3px solid currentColor !important;
}

/* 強制將第一欄 (常用) 縮小至極限 (40px)，並強制內容與標題置中 */
[data-testid="stTable"] table th:first-child, 
[data-testid="stTable"] table td:first-child {
    width: 40px !important;
    text-align: center !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🏢 建築原物料查詢系統")
col1, col2, col3 = st.columns([2, 2, 6])

# ================= 1. 分類管理 =================
with col1:
    h1, h2, h3 = st.columns([6, 2, 2])
    with h1: st.markdown("### 🗂️ 分類")
    
    if st.session_state.logged_in and st.session_state.main_cat:
        with h2:
            if st.button("✏️", key="btn_edit_m", help="編輯選擇的分類"): 
                st.session_state.edit_m = True; st.rerun()
        with h3:
            if st.button("🗑️", key="btn_del_m", help="刪除選擇的分類"):
                del st.session_state.db[st.session_state.main_cat]
                st.session_state.main_cat = None; st.session_state.sub_cat = None
                st.session_state.edit_m = False
                save_data(st.session_state.db); st.rerun()

    if st.session_state.logged_in and st.session_state.edit_m:
        ec1, ec2, ec3 = st.columns([6, 2, 2])
        new_m = ec1.text_input("新名稱", value=st.session_state.main_cat, label_visibility="collapsed")
        if ec2.button("💾", key="save_m"):
            if new_m and new_m != st.session_state.main_cat:
                st.session_state.db[new_m] = st.session_state.db.pop(st.session_state.main_cat)
                st.session_state.main_cat = new_m
                save_data(st.session_state.db)
            st.session_state.edit_m = False; st.rerun()
        if ec3.button("✖️", key="cancel_m"):
            st.session_state.edit_m = False; st.rerun()
        st.markdown("---")

    for cat in list(st.session_state.db.keys()):
        is_act = (st.session_state.main_cat == cat)
        if st.button(cat, key=f"m_{cat}", use_container_width=True, type="primary" if is_act else "secondary"):
            st.session_state.main_cat = cat; st.session_state.sub_cat = None
            st.session_state.edit_m = False; st.session_state.edit_s = False
            st.rerun()

    if st.session_state.logged_in:
        st.markdown("---")
        if not st.session_state.show_add_menu:
            if st.button("➕ 新增資料", use_container_width=True, type="primary"):
                st.session_state.show_add_menu = True; st.rerun()
        else:
            st.markdown("**選擇要新增的項目：**")
            ac1, ac2 = st.columns(2)
            if ac1.button("📁 分類", use_container_width=True): st.session_state.add_target = "main"; st.rerun()
            if ac2.button("📂 種類", use_container_width=True): st.session_state.add_target = "sub"; st.rerun()

            if st.session_state.add_target == "main":
                n_main = st.text_input("輸入新分類名稱", key="add_m_in")
                if st.button("儲存新分類", use_container_width=True) and n_main:
                    if n_main not in st.session_state.db:
                        st.session_state.db[n_main] = {}; save_data(st.session_state.db)
                        st.session_state.show_add_menu = False; st.session_state.add_target = None; st.rerun()
            
            elif st.session_state.add_target == "sub":
                if not st.session_state.main_cat:
                    st.warning("👈 請先在上方點選一個分類")
                else:
                    n_sub = st.text_input(f"在「{st.session_state.main_cat}」下新增種類", key="add_s_in")
                    if st.button("儲存新種類", use_container_width=True) and n_sub:
                        if n_sub not in st.session_state.db[st.session_state.main_cat]:
                            st.session_state.db[st.session_state.main_cat][n_sub] = []
                            save_data(st.session_state.db)
                            st.session_state.show_add_menu = False; st.session_state.add_target = None; st.rerun()

            if st.button("✖️ 取消新增", use_container_width=True):
                st.session_state.show_add_menu = False; st.session_state.add_target = None; st.rerun()

    # --- 系統登入與匯入區 ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("⚙️ 系統管理員"):
        if not st.session_state.logged_in:
            user = st.text_input("帳號")
            pwd = st.text_input("密碼", type="password")
            if st.button("登入", use_container_width=True):
                if user == "a2524" and pwd == "101487":
                    st.session_state.logged_in = True; st.rerun()
                else: st.error("錯誤")
        else:
            st.success("已登入")
            if st.button("登出", use_container_width=True): 
                st.session_state.logged_in = False; st.rerun()
            st.markdown("---")
            st.markdown("📥 **Excel 匯入**")
            up_file = st.file_uploader("選擇檔案", type=["xlsx", "xls"], label_visibility="collapsed")
            if up_file and st.button("執行匯入", use_container_width=True):
                try:
                    df_ex = pd.read_excel(up_file)
                    for _, r in df_ex.iterrows():
                        m, s = str(r.get('主分類','')).strip(), str(r.get('子分類','')).strip()
                        if m == 'nan' or s == 'nan': continue
                        if m not in st.session_state.db: st.session_state.db[m] = {}
                        if s not in st.session_state.db[m]: st.session_state.db[m][s] = []
                        st.session_state.db[m][s].append({"規格":str(r.get('規格','')), "單位重":str(r.get('單位重','')), "截面積":str(r.get('截面積',''))})
                    save_data(st.session_state.db); st.success("完成"); st.rerun()
                except Exception as e: st.error(f"錯誤: {e}")

# ================= 2. 種類管理 =================
with col2:
    if st.session_state.main_cat:
        sh1, sh2, sh3 = st.columns([6, 2, 2])
        with sh1: st.markdown(f"### 📂 種類")
        
        if st.session_state.logged_in and st.session_state.sub_cat:
            with sh2:
                if st.button("✏️", key="btn_edit_s", help="編輯選擇的種類"): 
                    st.session_state.edit_s = True; st.rerun()
            with sh3:
                if st.button("🗑️", key="btn_del_s", help="刪除選擇的種類"):
                    del st.session_state.db[st.session_state.main_cat][st.session_state.sub_cat]
                    st.session_state.sub_cat = None; st.session_state.edit_s = False
                    save_data(st.session_state.db); st.rerun()

        if st.session_state.logged_in and st.session_state.edit_s:
            sc1, sc2, sc3 = st.columns([6, 2, 2])
            new_s = sc1.text_input("新名稱", value=st.session_state.sub_cat, label_visibility="collapsed")
            if sc2.button("💾", key="save_s"):
                if new_s and new_s != st.session_state.sub_cat:
                    st.session_state.db[st.session_state.main_cat][new_s] = st.session_state.db[st.session_state.main_cat].pop(st.session_state.sub_cat)
                    st.session_state.sub_cat = new_s
                    save_data(st.session_state.db)
                st.session_state.edit_s = False; st.rerun()
            if sc3.button("✖️", key="cancel_s"):
                st.session_state.edit_s = False; st.rerun()
            st.markdown("---")

        subs = st.session_state.db[st.session_state.main_cat]
        for sub in list(subs.keys()):
            is_sub_act = (st.session_state.sub_cat == sub)
            if st.button(sub, key=f"s_{sub}", use_container_width=True, type="primary" if is_sub_act else "secondary"):
                st.session_state.sub_cat = sub
                st.session_state.edit_s = False; st.rerun()

# ================= 3. 明細展示 =================
with col3:
    if st.session_state.sub_cat:
        st.markdown(f"### 📊 {st.session_state.sub_cat} 明細")
        data = st.session_state.db[st.session_state.main_cat][st.session_state.sub_cat]
        df = pd.DataFrame(data)
        
        if not df.empty:
            if "規格" not in df.columns: df["規格"] = ""
            if "單位重" not in df.columns: df["單位重"] = ""
            if "截面積" not in df.columns: df["截面積"] = ""
            
            # 將 * 或是 V 獨立解析到「常用」欄位，並過濾掉前綴
            def parse_common(val):
                val_str = str(val).strip()
                return "V" if val_str.startswith("*") or val_str.upper().startswith("V") else ""
            
            def clean_spec(val):
                val_str = str(val).strip()
                if val_str.startswith("*") or val_str.upper().startswith("V"):
                    return val_str[1:].strip()
                return val_str

            df["常用"] = df["規格"].apply(parse_common)
            df["規格"] = df["規格"].apply(clean_spec)
        else:
            df = pd.DataFrame(columns=["常用", "規格", "單位重", "截面積"])
            
        df = df[["常用", "規格", "單位重", "截面積"]]

        def style_fn(row):
            # 只要是 V (不分大小寫) 就整列高亮黃底
            if str(row.get('常用', '')).strip().upper() == 'V':
                return ['background-color: #ffe066; color: black; font-weight: normal !important'] * len(row)
            return [''] * len(row)
            
        styled = df.style.hide(axis="index").apply(style_fn, axis=1).set_properties(**{'font-size':'28px','padding':'15px'})
        styled = styled.set_properties(subset=['常用', '單位重', '截面積'], **{'text-align':'center !important'})
        styled = styled.set_table_styles([{'selector':'th','props':[('text-align','center !important')]}])

        if st.session_state.logged_in:
            st.info("✏️ **編輯模式**：在「常用」欄位輸入 `V` 即可設定為高亮常用規格。")
            
            edited = st.data_editor(
                styled, 
                num_rows="dynamic", 
                use_container_width=True, 
                hide_index=True,
                column_config={"常用": st.column_config.TextColumn("常用", width="small")}
            )
            
            if st.button("💾 儲存表格修改", type="primary"):
                save_list = []
                edited_dicts = edited.to_dict('records')
                for d in edited_dicts:
                    spec = str(d.get("規格", ""))
                    is_common = str(d.get("常用", "")).strip().upper() == "V"
                    
                    # 避免重複疊加前綴
                    clean_s = spec
                    if clean_s.startswith('*') or clean_s.upper().startswith('V'):
                        clean_s = clean_s[1:].strip()
                        
                    final_spec = "V" + clean_s if is_common else clean_s
                    
                    save_list.append({
                        "規格": final_spec,
                        "單位重": str(d.get("單位重", "")),
                        "截面積": str(d.get("截面積", ""))
                    })
                    
                st.session_state.db[st.session_state.main_cat][st.session_state.sub_cat] = save_list
                save_data(st.session_state.db)
                st.success("已儲存！")
                st.rerun()

            # ===== 即時預覽區 =====
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 👀 檢視模式預覽")
            st.caption("此為一般使用者看到的最終畫面，儲存後即時更新：")
            st.table(styled)
        else: 
            # 訪客模式直接看表
            st.table(styled)
    else: 
        st.info("請由左側選擇分類與種類")