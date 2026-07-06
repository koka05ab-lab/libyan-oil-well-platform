import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import sqlite3
# فرضاً أن هذه هي البيانات القادمة من قاعدة البيانات SQLite الخاصة بك
# تأكد من مطابقة أسماء الأعمدة مع كودك الحالي
@st.cache_data
def load_well_data():
    # الاتصال بقاعدة بيانات الآبار
    conn = sqlite3.connect("oil_wells.db")
    
    # جلب كافة البيانات الـ 16 من جدول الآبار
    query = "SELECT * FROM wells"
    df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df
    

df_wells = load_well_data()

st.title("🌍 المراقبة الجغرافية اللحظية وتحديث قاعدة البيانات (Live SQLite GIS)")

# =========================================================
# 1. شريط الفلاتر الجانبي (Sidebar Filters)
# =========================================================
st.sidebar.header("🔍 فلاتر التحكم بالخريطة")

# فلتر الحقول
all_fields = ['الكل'] + list(df_wells['Field'].unique())
selected_field = st.sidebar.selectbox("اختر الحقل النفطي:", all_fields)

# فلتر حالة الخطر
all_status = ['الكل', 'Safe', 'Critical']
selected_status = st.sidebar.selectbox("حالة البئر الجغرافية:", all_status)

# تطبيق الفلاتر على البيانات
df_filtered = df_wells.copy()
if selected_field != 'الكل':
    df_filtered = df_filtered[df_filtered['Field'] == selected_field]
if selected_status != 'الكل':
    df_filtered = df_filtered[df_filtered['Risk_Level'] == selected_status]


# =========================================================
# 2. بناء الخريطة المتقدمة باستخدام Folium
# =========================================================
st.subheader("🗺️ خريطة حقول النفط التفاعلية")

# تحديد مركز الخريطة بناءً على الآبار المتاحة
if not df_filtered.empty:
    center_lat = df_filtered['Latitude'].mean()
    center_lon = df_filtered['Longitude'].mean()
else:
    center_lat, center_lon = 28.0000, 22.0000 # مركز افتراضي للصحراء الليبية

# إنشاء الخريطة وإضافة خيار القمر الصناعي الاساسي وخريطة التضاريس
m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles=None)

# إضافة الطبقات الجغرافية (Layers)
folium.TileLayer('OpenStreetMap', name='خريطة الشوارع/الحدود').add_to(m)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri, DigitalGlobe, GeoEye, Earthstar Geographics',
    name='قمر صناعي (Esri Satellite)'
).add_to(m)

# إضافة الآبار كـ Markers ملونة تفاعلية
for idx, row in df_filtered.iterrows():
    # تحديد اللون بناءً على حالة الخطر
    color = 'green' if row['Risk_Level'] == 'Safe' else 'red'
    icon_type = 'info-sign' if row['Risk_Level'] == 'Safe' else 'exclamation-sign'
    
    # تصميم نافذة المعلومات المحسنة (Popup HTML)
    popup_html = f"""
    <div style="font-family: 'Arial', sans-serif; direction: rtl; text-align: right; width: 200px;">
        <h4 style="color: #2c3e50; margin-bottom: 5px;">🛢️ {row['Well_Name']}</h4>
        <hr style="margin: 5px 0;">
        <b>الحقل:</b> {row['Field']}<br>
        <b>الضغط:</b> {row['Pressure_PSI']} PSI<br>
        <b>الحرارة:</b> {row['Temperature_C']} °C<br>
        <b>حالة الخطر:</b> <span style="color: {color}; font-weight: bold;">{row['Risk_Level']}</span>
    </div>
    """
    
    # إضافة النقطة إلى الخريطة
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f"البئر: {row['Well_Name']} ({row['Risk_Level']})",
        icon=folium.Icon(color=color, icon=icon_type)
    ).add_to(m)

# تفعيل أداة التحكم بالطبقات لتبديل النمط من زاوية الخريطة
folium.LayerControl().add_to(m)

# عرض الخريطة داخل Streamlit
st_folium(m, width=800, height=500)

# دليل الألوان (Legend) أسفل الخريطة
st.markdown("""
<div style="display: flex; gap: 20px; justify-content: center; background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
    <div><span style="color: green; font-size: 20px;">●</span> آبار مستقرة (Safe)</div>
    <div><span style="color: red; font-size: 20px;">●</span> آبار حرجة / خطر (Critical)</div>
</div>
""", unsafe_allow_html=True)
