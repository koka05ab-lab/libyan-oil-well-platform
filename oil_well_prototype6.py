import streamlit as st
import pandas as pd
import pydeck as pdk
import sqlite3
import os

# إعدادات الصفحة العامة المنفصلة
st.set_page_config(page_title="منصة إدارة الآبار النفطية الليبية المتكاملة V4", layout="wide")

st.title(" Libyan Oil Wells Integrated Enterprise Platform - V4")
st.subheader("منصة التحكم الشاملة: مراقبة جغرافية، قاعدة بيانات مستقرة، ومساعد صيانة ذكي")
st.write("---")

# --- [المرحلة الثالثة: إعداد وإدارة قاعدة البيانات SQLite] ---
DB_NAME = "oil_fields.db"

def init_database():
    """إنشاء قاعدة البيانات وتغذيتها بالبيانات الأساسية إذا لم تكن موجودة"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # إنشاء جدول الآبار
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wells (
        well_name TEXT PRIMARY KEY,
        latitude REAL,
        longitude REAL,
        target_pressure REAL,
        target_temp REAL,
        current_pressure REAL,
        current_temp REAL
    )
    """)
    
    # التأكد من وجود البيانات الـ 16
    cursor.execute("SELECT COUNT(*) FROM wells")
    if cursor.fetchone()[0] == 0:
        wells_data = []
        # آبار حقل السرير
        for i in range(1, 9):
            wells_data.append((f'Well-SR-{i}', 28.15 + (i*0.01), 22.45 + (i*0.01), 3200.0, 85.0, 3200.0, 85.0))
        # آبار حقل مسلة
        for i in range(1, 9):
            wells_data.append((f'Well-MS-{i}', 27.85 + (i*0.01), 22.15 + (i*0.01), 3000.0, 80.0, 3000.0, 80.0))
            
        cursor.executemany("""
        INSERT INTO wells VALUES (?, ?, ?, ?, ?, ?, ?)
        """, wells_data)
        conn.commit()
    conn.close()

# تشغيل دالة بناء قاعدة البيانات
init_database()

def load_data_from_db():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM wells", conn)
    conn.close()
    return df

def update_well_in_db(well_name, pressure, temp):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE wells 
    SET current_pressure = ?, current_temp = ? 
    WHERE well_name = ?
    """, (pressure, temp, well_name))
    conn.commit()
    conn.close()

# جلب البيانات الطازجة من قاعدة البيانات
df_wells = load_data_from_db()

# --- [محرك الذكاء الاصطناعي لحساب خطر العطل الجغرافي] ---
def analyze_well_health(row):
    p_dev = abs(row['current_pressure'] - row['target_pressure']) / row['target_pressure']
    t_dev = abs(row['current_temp'] - row['target_temp']) / row['target_temp']
    risk_score = (p_dev * 0.6 + t_dev * 0.4) * 100
    
    if row['current_pressure'] == 0:
        return pd.Series(['متوقف عن الإنتاج', [128, 128, 128, 200], 0.0])
    elif risk_score < 10:
        return pd.Series(['نشط وآمن 👍', [0, 255, 0, 200], risk_score])
    elif risk_score < 22:
        return pd.Series(['تحت المراقبة / تذبذب ⚠️', [255, 165, 0, 200], risk_score])
    else:
        return pd.Series(['خطر عطل حرج 🚨', [255, 0, 0, 255], risk_score])

res = df_wells.apply(analyze_well_health, axis=1)
df_wells['Status'] = res[0]
df_wells['Color'] = res[1]
df_wells['Risk_Score'] = res[2]

# --- [المرحلة الخامسة: شريط المساعد الفني الذكي AI Chatbot] ---
with st.sidebar:
    st.markdown("### 💬 مساعد الصيانة الذكي (AI Chatbot)")
    st.write("استشر المساعد الفني حول كيفية التعامل مع مشاكل ضغط وحرارة الآبار:")
    
    user_question = st.text_input("اكتب سؤالك الفني هنا (مثال: كيف أتصرف عند ارتفاع حرارة البئر؟):")
    if user_question:
        # محاكاة رد ذكي بناءً على الكتيبات الهندسية للنفط والغاز
        if "حرارة" in user_question or "الحرارة" in user_question:
            st.warning("🤖 **رد المساعد الذكي:** ارتفاع الحرارة المفرط يشير إلى زيادة الاحتكاك في المضخة الغاطسة (ESP). يُنصح بتقليل تدفق الخنق (Choke Valve) تدريجياً والتحقق من التبريد السائل فوراً لتفادي احتراق المحرك.")
        elif "ضغط" in user_question or "الضغط" in user_question:
            st.warning("🤖 **رد المساعد الذكي:** الارتفاع الحاد في الضغط المرتد (Backpressure) يدل على انسداد جزئي في خط التدفق أو صمام الأمان العلوي. يرجى مراجعة الصمامات قبل حدوث هبوط إنتاجي.")
        else:
            st.info("🤖 **رد المساعد الذكي:** أهلاً بك مهندس. لضمان سلامة الآبار، يرجى الحفاظ على القراءات اللحظية ضمن نطاق انحراف لا يتعدى 10% من الأهداف التشغيلية المحددة في قاعدة البيانات.")

# تقسيم الشاشة الرئيسية لـ Streamlit
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### ⚙️ لوحة التحكم وتحديث قاعدة البيانات")
    
    selected_well = st.selectbox("اختر البئر المراد إدارته وفحصه عينات برمجية:", df_wells['well_name'])
    idx = df_wells[df_wells['well_name'] == selected_well].index[0]
    well_info = df_wells.loc[idx]
    
    st.write("📊 **تعديل وتحديث القراءات الفعلية في قاعدة البيانات السحابية:**")
    
    new_p = st.slider(f"الضغط الفعلي لبئر ({selected_well}) - PSI", 
                      min_value=0, max_value=6000, 
                      value=int(well_info['current_pressure']), step=50)
    
    new_t = st.slider(f"درجة الحرارة الفعلية (°C)", 
                      min_value=20, max_value=150, 
                      value=int(well_info['current_temp']), step=1)
    
    # زر الحفظ وتحديث قاعدة البيانات بشكل مستقر
    if st.button("💾 حفظ التحديثات في قاعدة البيانات المستقرة"):
        update_well_in_db(selected_well, new_p, new_t)
        st.success(f"تم بنجاح حفظ قراءات {selected_well} المحدثة في ملف قاعدة البيانات!")
        st.rerun()
        
    st.markdown(f"""
    <div style="background-color:#1e1e1e; padding:15px; border-radius:10px; border-left: 5px solid rgb({well_info['Color'][0]},{well_info['Color'][1]},{well_info['Color'][2]}); marginTop:15px;">
        <h4>📋 تقرير تحليل البيانات (Database & AI Status):</h4>
        <b>الحالة المفسرة:</b> {well_info['Status']}<br>
        <b>الضغط في القاعدة:</b> {well_info['current_pressure']} PSI (الهدف: {well_info['target_pressure']})<br>
        <b>الحرارة في القاعدة:</b> {well_info['current_temp']} °C (الهدف: {well_info['target_temp']})<br>
        <b>معامل احتمالية المخاطر الجغرافية:</b> {well_info['Risk_Score']:.1f}%
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    st.metric("إجمالي الآبار المستهدفة في الحقول 🗺️", len(df_wells))

with col2:
    st.markdown("### 🌍 المراقبة الجغرافية اللحظية من قاعدة البيانات (Live SQLite GIS)")
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        df_wells,
        get_position="[longitude, latitude]",
        get_color="Color",
        get_radius=1800,  
        pickable=True,
    )
    
    view_state = pdk.ViewState(
        latitude=df_wells['latitude'].mean(),
        longitude=df_wells['longitude'].mean(),
        zoom=7.5,
        pitch=20,
    )
    
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="carto_dark",
        tooltip={"text": "البئر: {well_name}\nالحالة: {Status}\nاحتمالية العطل: {Risk_Score:.1f}%"}
    )
    
    st.pydeck_chart(r)

st.write("---")
st.caption("🔒 منصة سيادية متكاملة V4 - مدمجة بقاعدة بيانات SQLite داخلية وخوارزميات تنبؤية ذكية لإدارة آبار قطاع النفط.")