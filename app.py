import streamlit as st
import pandas as pd
import json
import os
import base64
from PIL import Image

# 1. 取得目前 app.py 檔案所在的資料夾絕對路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 將資料庫與圖片資料夾定位在該絕對路徑下
DATA_FILE = os.path.join(BASE_DIR, "building_data.json")
IMAGE_DIR = os.path.join(BASE_DIR, "uploaded_images")

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# ================= 輔助與資料清洗函式 =================
def image_to_base64(img_path):
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def parse_common(val):
    val_str = str(val).strip()
    return "V" if val_str.startswith("*") or val_str.upper().startswith("V") else ""

def clean_spec(val):
    val_str = str(val).strip()
    if val_str.startswith("*") or val_str.upper().startswith("V"):
        return val_str[1:].strip()
    return val_str

def load_data():
    if not os.path.exists(DATA_FILE):
        # 將預設資料修改為完全空白的結構
        default_data = {
            "原料": {},
            "物料": {}, 
            "消耗品": {}
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
            
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_db = json.load(f)
        # 資料結構與舊欄位自動遷移機制
        for m_cat, sub_dict in raw_db.items():
            for s_cat, content in sub_dict.items():
                if isinstance(content, list):
                    raw_db[m_cat][s_cat] = {"代表圖": "", "資料": content}
                
                if m_cat != "原料":
                    for item in raw_db[m_cat][s_cat].get("資料", []):
                        if "直徑(mm)" in item:
                            item["材質/顏色/組成/其他資訊"] = item.pop("直徑(mm)")
                        if "備註" in item:
                            item["包裝方式"] = item.pop("備註")
        return raw_db

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= 檢視模式 HTML =================
def get_view_html(data_dicts, is_raw_cat):
    df = pd.DataFrame(data_dicts)
    base_cols = ["規格", "單位重", "截面積"] if is_raw_cat else ["規格", "材質/顏色/組成/其他資訊", "包裝方式"]
    
    if df.empty:
        df = pd.DataFrame(columns=["常用"] + base_cols)
    else:
        for c in base_cols:
            if c not in df.columns: df[c] = ""
        df["常用"] = df["規格"].apply(parse_common)
        df["規格"] = df["規格"].apply(clean_spec)
        df = df[["常用"] + base_cols]
        
    def style_fn(row):
        if str(row.get('常用', '')).strip().upper() == 'V':
            return ['background-color: #ffe066; color: black; font-weight: normal !important'] * len(row)
        return ['font-weight: normal !important'] * len(row)
        
    sty = df.style.hide(axis="index").apply(style_fn, axis=1).set_properties(**{
        'font-size':'22px',       
        'padding-top':'8px',      
        'padding-bottom':'8px', 
        'padding-left': '15px',   
        'padding-right': '15px',
        'font-weight': 'normal !important'
    })
    sty = sty.set_properties(subset=['常用'] + base_cols, **{'text-align':'center !important', 'vertical-align':'middle !important'})
    sty = sty.set_table_styles([{'selector':'th','props':[('text-align','center !important'), ('font-weight', 'normal !important')]}])
    
    return f'<div class="view-table">{sty.to_html(escape=False)}</div>'

# ================= 初始化 =================
if 'db' not in st.session_state: st.session_state.db = load_data()
if 'main_cat' not in st.session_state: st.session_state.main_cat = None
if 'sub_cat' not in st.session_state: st.session_state.sub_cat = None
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'edit_m' not in st.session_state: st.session_state.edit_m = False
if 'edit_s' not in st.session_state: st.session_state.edit_s = False
if 'show_add_menu' not in st.session_state: st.session_state.show_add_menu = False
if 'add_target' not in st.session_state: st.session_state.add_target = None

st.set_page_config(page_title="建築原物料查詢系統", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
header { display: none !important; }
html, body { overflow-y: scroll !important; }
html, body, p, div, span, h1, h2, h3, h4, h5, h6, table, th, td, input, select, textarea, button {
    font-family: '華康中特圓體', 'Microsoft JhengHei', sans-serif !important;
    font-weight: normal !important;
}
[data-testid="stIconMaterial"] { font-family: "Material Symbols Rounded" !important; }
div[data-testid="stButton"] button[kind="primary"] {
    transform: scale(0.85) !important; opacity: 0.4 !important; transition: all 0.3s ease !important;
}
[data-testid="column"]:nth-of-type(3) {
    border: 3px solid currentColor !important;
    border-radius: 12px;
    padding: 20px;
    min-height: 85vh;
    background-color: rgba(128, 128, 128, 0.05) !important; 
}

/* 檢視模式表格樣式 */
.view-table table { 
    width: 100% !important; 
    table-layout: fixed !important; 
    border-collapse: collapse !important; 
    border: 2px solid currentColor !important;
}
.view-table th, .view-table td { 
    border: 1px solid currentColor !important; 
    vertical-align: middle !important;
    line-height: 1.2 !important; 
    font-weight: normal !important;
}
.view-table thead th { 
    border-bottom: 3px solid currentColor !important; 
    padding-top: 10px !important;    
    padding-bottom: 10px !important;
    font-weight: normal !important;
}
.view-table table th:first-child, .view-table table td:first-child {
    width: 40px !important; text-align: center !important;
}
.header-img-container img {
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

[data-testid="stDataFrame"] div[role="row"] {
    min-height: 35px !important; 
}
[data-testid="stDataFrame"] * {
    font-weight: normal !important;
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
            if st.button("✏️", key="btn_edit_m"): st.session_state.edit_m = True; st.rerun()
        with h3:
            if st.button("🗑️", key="btn_del_m"):
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
            if st.button("➕ 新增資料", use_container_width=True, type="primary"): st.session_state.show_add_menu = True; st.rerun()
        else:
            st.markdown("**選擇新增：**")
            ac1, ac2 = st.columns(2)
            if ac1.button("📁 分類", use_container_width=True): st.session_state.add_target = "main"; st.rerun()
            if ac2.button("📂 種類", use_container_width=True): st.session_state.add_target = "sub"; st.rerun()

            if st.session_state.add_target == "main":
                n_main = st.text_input("新分類名稱", key="add_m_in")
                if st.button("儲存", use_container_width=True) and n_main:
                    if n_main not in st.session_state.db:
                        st.session_state.db[n_main] = {}; save_data(st.session_state.db)
                        st.session_state.show_add_menu = False; st.session_state.add_target = None; st.rerun()
            elif st.session_state.add_target == "sub":
                if not st.session_state.main_cat: st.warning("請先選擇分類")
                else:
                    n_sub = st.text_input(f"新增種類", key="add_s_in")
                    if st.button("儲存", use_container_width=True) and n_sub:
                        if n_sub not in st.session_state.db[st.session_state.main_cat]:
                            st.session_state.db[st.session_state.main_cat][n_sub] = {"代表圖": "", "資料": []}
                            save_data(st.session_state.db)
                            st.session_state.show_add_menu = False; st.session_state.add_target = None; st.rerun()
            if st.button("✖️ 取消", use_container_width=True):
                st.session_state.show_add_menu = False; st.session_state.add_target = None; st.rerun()

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
                    df_ex.columns = [str(c).strip() for c in df_ex.columns]
                    def clean_val(v): return "" if pd.isna(v) else str(v).strip()

                    for _, r in df_ex.iterrows():
                        m = clean_val(r.get('主分類'))
                        s = clean_val(r.get('子分類'))
                        if not m or not s: continue
                        if m not in st.session_state.db: st.session_state.db[m] = {}
                        if s not in st.session_state.db[m]: st.session_state.db[m][s] = {"代表圖": "", "資料": []}
                        
                        record = {"規格": clean_val(r.get('規格'))}
                        if m == "原料":
                            record["單位重"] = clean_val(r.get('單位重'))
                            record["截面積"] = clean_val(r.get('截面積'))
                        else:
                            record["材質/顏色/組成/其他資訊"] = clean_val(r.get('材質/顏色/組成/其他資訊', r.get('直徑(mm)', '')))
                            record["包裝方式"] = clean_val(r.get('包裝方式', r.get('備註', '')))
                            
                        st.session_state.db[m][s]["資料"].append(record)
                    save_data(st.session_state.db); st.success("完成"); st.rerun()
                except Exception as e: st.error(f"錯誤: {e}")

# ================= 2. 種類管理 =================
with col2:
    if st.session_state.main_cat:
        sh1, sh2, sh3 = st.columns([6, 2, 2])
        with sh1: st.markdown(f"### 📂 種類")
        
        if st.session_state.logged_in and st.session_state.sub_cat:
            with sh2:
                if st.button("✏️", key="btn_edit_s"): st.session_state.edit_s = True; st.rerun()
            with sh3:
                if st.button("🗑️", key="btn_del_s"):
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
        is_raw_cat = (st.session_state.main_cat == "原料")
        cat_data = st.session_state.db[st.session_state.main_cat][st.session_state.sub_cat]
        data_list = cat_data.get("資料", [])
        
        th1, th2 = st.columns([6, 4])
        with th1:
            st.markdown(f"### 📊 {st.session_state.sub_cat} 明細")
        
        with th2:
            if not is_raw_cat:
                if st.session_state.logged_in:
                    up_img = st.file_uploader("📸 變更代表圖", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
                    if up_img is not None:
                        save_path = os.path.join(IMAGE_DIR, f"rep_{st.session_state.sub_cat}_{up_img.name}")
                        with open(save_path, "wb") as f: f.write(up_img.getbuffer())
                        st.session_state.db[st.session_state.main_cat][st.session_state.sub_cat]["代表圖"] = save_path
                        save_data(st.session_state.db)
                        st.rerun()
                        
                current_img = cat_data.get("代表圖", "")
                if current_img:
                    try:
                        if current_img.startswith('http'):
                            img_html = f'<img src="{current_img}" style="width: 4cm; height: 4cm; object-fit: contain; background: rgba(255,255,255,0.05);">'
                        else:
                            img_html = f'<img src="data:image/jpeg;base64,{image_to_base64(current_img)}" style="width: 4cm; height: 4cm; object-fit: contain; background: rgba(255,255,255,0.05);">'
                        st.markdown(f'<div class="header-img-container" style="display: flex; justify-content: flex-end;">{img_html}</div>', unsafe_allow_html=True)
                    except: pass

        if st.session_state.logged_in:
            df = pd.DataFrame(data_list)
            base_cols = ["規格", "單位重", "截面積"] if is_raw_cat else ["規格", "材質/顏色/組成/其他資訊", "包裝方式"]
            
            if df.empty:
                df = pd.DataFrame(columns=["常用"] + base_cols)
            else:
                for c in base_cols:
                    if c not in df.columns: df[c] = ""
                df["常用"] = df["規格"].apply(parse_common)
                df["規格"] = df["規格"].apply(clean_spec)
                df = df[["常用"] + base_cols]

            def s_fn(row):
                if str(row.get('常用', '')).strip().upper() == 'V':
                    return ['background-color: #ffe066; color: black; font-weight: normal !important'] * len(row)
                return ['font-weight: normal !important'] * len(row)
                
            styled = df.style.hide(axis="index").apply(s_fn, axis=1).set_properties(**{
                'font-size':'22px', 
                'padding-top':'8px', 
                'padding-bottom':'8px',
                'padding-left': '15px',
                'padding-right': '15px',
                'font-weight': 'normal !important'
            })
            styled = styled.set_properties(subset=['常用'] + base_cols, **{'text-align':'center !important'})
            
            c_conf = {"常用": st.column_config.TextColumn("常用", width="small")}

            edited = st.data_editor(
                styled, 
                num_rows="dynamic", 
                use_container_width=True, 
                hide_index=True,
                column_config=c_conf
            )
            
            if st.button("💾 儲存表格修改", type="primary"):
                save_list = []
                for d in edited.to_dict('records'):
                    spec = str(d.get("規格", ""))
                    is_common = str(d.get("常用", "")).strip().upper() == "V"
                    
                    clean_s = spec
                    if clean_s.startswith('*') or clean_s.upper().startswith('V'): clean_s = clean_s[1:].strip()
                    final_spec = "V" + clean_s if is_common else clean_s
                    
                    record = {"規格": final_spec}
                    if is_raw_cat:
                        record["單位重"] = str(d.get("單位重", ""))
                        record["截面積"] = str(d.get("截面積", ""))
                    else:
                        record["材質/顏色/組成/其他資訊"] = str(d.get("材質/顏色/組成/其他資訊", ""))
                        record["包裝方式"] = str(d.get("包裝方式", ""))
                    save_list.append(record)
                    
                st.session_state.db[st.session_state.main_cat][st.session_state.sub_cat]["資料"] = save_list
                save_data(st.session_state.db)
                st.success("已儲存！")
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 👀 檢視模式預覽")
            st.markdown(get_view_html(st.session_state.db[st.session_state.main_cat][st.session_state.sub_cat]["資料"], is_raw_cat), unsafe_allow_html=True)
        else: 
            st.markdown(get_view_html(data_list, is_raw_cat), unsafe_allow_html=True)
    else: 
        st.info("請由左側選擇分類與種類")