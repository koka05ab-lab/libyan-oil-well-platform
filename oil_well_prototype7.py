import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. إعدادات الصفحة العامة وتحسين المظهر
st.set_page_config(
    page_title="منصة مراقبة الآبار النفطية الليبية",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تحسين المظهر باستخدام CSS مخصص لتنسيق الحقول والاتجاهات (RTL)
st.markdown("""
    <style>
    .reportview-container { direction: rtl; text-align: right; }
    .sidebar .sidebar-content { direction: rtl; text-align: right; }
    div.stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-right: 5px solid #007bff;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 2. دالة البيانات الـ 16 الرئيسية المستخرجة من التقرير
@st.cache_data
def load_well_data():
    data = {
        'Well_Name': [
            'HH86-65', 'H54-65', 'L-028HR', 'Z-13', 
            'J-03', 'B1-LP3D', 'T27-13', 
            'R11', 'C1-16/4 (BESS-3)', 'B2-16/4', 'J1-4/16',
            'I-30INC186', 'J1-4/130', 'A1-2/130', 
            'A1-69/02', 'B1-106/4'
        ],
        'Field': [
            'حقل مسلة', 'حقل مسلة', 'حقل السرير', 'حقل البيضاء',
            'حقل متخندوش', 'حقل الخير', 'حقل الاستلهاب - دور مرادة',
            'مليتة', 'البلوك D / 41 MN هـ ع', 'بحر السلام 2', 'البلوك D البحري',
            'الشرارة / NC186', 'حوض مرزق', 'قرب الشرارة Neser',
            'حوض غدامس', 'شرق حوض سرت'
        ],
        'Latitude': [
            27.8100, 27.8500, 27.6500, 28.4300,
            26.5500, 26.2100, 29.2300,
            32.8800, 33.1500, 33.3000, 33.0500,
            25.6800, 25.4500, 25.8000,
            29.6500, 29.1000
        ],
        'Longitude': [
            22.4200, 22.4800, 22.5000, 18.9100,
            15.3300, 15.9500, 19.1200,
            12.2400, 12.3500, 12.1000, 12.4500,
            13.1200, 12.9000, 13.0500,
            11.2000, 21.4000
        ],
        'Pressure_PSI': [3100, 2950, 3200, 1800, 2400, 2650, 1950, 4100, 3890, 4200, 3950, 2800, 2750, 2900, 3300, 2100],
        'Temperature_C': [82, 80, 85, 71, 68, 74, 70, 95, 92, 98, 94, 76, 73, 78, 88, 72],
        'Risk_Level': ['Safe', 'Safe', 'Safe', 'Critical', 'Safe', 'Safe', 'Safe', 'Safe', 'Safe', 'Safe', 'Safe', 'Safe', 'Safe', 'Safe', 'Safe', 'Critical']
    }
    return pd.DataFrame(data)

df_wells = load_well_data()

# 3. شريط التحكم الجانبي التفاعلي (Sidebar)
st.sidebar.header("🔍 لوحة التحكم والفلاتر")

# فلتر الحقول النفطية
all_fields = ['الكل'] + list(df_wells['Field'].unique())
selected_field = st.sidebar.selectbox("اختر الحقل النفطي:", all_fields)

# فلتر درجة الخطورة
risk_options = ['الكل', 'Safe', 'Critical']
selected_risk = st.sidebar.selectbox("حالة البئر الجغرافية:", risk_options)

# ميزة مميزة: إضافة محاكي لإدخال بئر جديد تلقائياً
st.sidebar.markdown("---")
st.sidebar.subheader("➕ محاكاة إضافة بئر جديد")
with st.sidebar.form("add_well_form"):
    new_name = st.text_input("اسم البئر:", "Well-NEW-01")
    new_field = st.text_input("الحقل النفطي:", "حوض سرت الجديد")
    new_lat = st.number_input("خط العرض (Lat):", value=29.0)
    new_lon = st.number_input("خط الطول (Lon):", value=18.0)
    new_press = st.slider("الضغط (PSI):", 1000, 5000, 3000)
    new_temp = st.slider("الحرارة (C°):", 40, 120, 75)
    new_risk = st.selectbox("حالة المخاطرة:", ["Safe", "Critical"])
    submit_btn = st.form_submit_button("إضافة وتحديث المنصة")

if submit_btn:
    new_row = pd.DataFrame([{
        'Well_Name': new_name, 'Field': new_field, 'Latitude': new_lat, 'Longitude': new_lon,
        'Pressure_PSI': new_press, 'Temperature_C': new_temp, 'Risk_Level': new_risk
    }])
    df_wells = pd.concat([df_wells, new_row], ignore_index=True)

# تصفية البيانات برمجياً بناءً على اختيارات المستخدم
filtered_df = df_wells.copy()
if selected_field != 'الكل':
    filtered_df = filtered_df[filtered_df['Field'] == selected_field]
if selected_risk != 'الكل':
    filtered_df = filtered_df[filtered_df['Risk_Level'] == selected_risk]

# 4. الواجهة الرئيسية والعناوين
st.title("🛢️ المنصة الوطنية الذكية لمراقبة الآبار النفطية الليبية")
st.subheader("المراقبة الجغرافية اللحظية وتحليل بيانات الضغط والحرارة (Live GIS Platform)")

# 5. قسم بطاقات الأداء الرقمية الذكية (KPI Metrics)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("إجمالي الآبار المعروضة", len(filtered_df))
with col2:
    critical_count = len(filtered_df[filtered_df['Risk_Level'] == 'Critical'])
    st.metric("الآبار الحرجة (Critical)", critical_count, delta=f"{critical_count} تحتاج صيانة", delta_color="inverse")
with col3:
    avg_press = int(filtered_df['Pressure_PSI'].mean()) if not filtered_df.empty else 0
    st.metric("متوسط الضغط الحركي", f"{avg_press} PSI")
with col4:
    avg_temp = int(filtered_df['Temperature_C'].mean()) if not filtered_df.empty else 0
    st.metric("متوسط درجة الحرارة", f"{avg_temp} C°")

st.markdown("---")

# 6. قسم الخريطة التفاعلية والرسومات البيانية (توزيع جنباً إلى جنب)
map_col, chart_col = st.columns([2, 1])

with map_col:
    st.subheader("🗺️ التوزع الجغرافي للآبار والمنشآت")
    
    # تحديد نقطة سنتر الخريطة تلقائياً حسب البيانات المتاحة
    start_lat = filtered_df['Latitude'].mean() if not filtered_df.empty else 28.0
    start_lon = filtered_df['Longitude'].mean() if not filtered_df.empty else 17.0
    
    m = folium.Map(location=[start_lat, start_lon], zoom_start=6, tiles="OpenStreetMap")
    
    # إضافة علامات الآبار ملونة وذكية
    for _, row in filtered_df.iterrows():
        color = 'red' if row['Risk_Level'] == 'Critical' else 'green'
        icon_type = 'exclamation-sign' if row['Risk_Level'] == 'Critical' else 'info-sign'
        
        popup_html = f"""
        <div style='direction: rtl; text-align: right; font-family: Arial;'>
            <b>البئر:</b> {row['Well_Name']}<br>
            <b>الحقل:</b> {row['Field']}<br>
            <b>الضغط:</b> {row['Pressure_PSI']} PSI<br>
            <b>الحرارة:</b> {row['Temperature_C']} C°<br>
            <b>الحالة:</b> <span style='color:{color}; font-weight:bold;'>{row['Risk_Level']}</span>
        </div>
        """
        
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=color, icon=icon_type)
        ).add_to(m)
        
    st_folium(m, width="100%", height=450, key="oil_map")

with chart_col:
    st.subheader("📊 مقارنة ضغط الآبار (PSI)")
    if not filtered_df.empty:
        # رسم بياني تفاعلي لمقارنة الضغوط
        chart_data = filtered_df.set_index('Well_Name')[['Pressure_PSI']]
        st.bar_chart(chart_data, height=410)
    else:
        st.info("لا توجد بيانات كافية لعرض الرسم البياني.")

st.markdown("---")

# 7. قسم جدول البيانات التفاعلي المتقدم للتحميل والبحث
st.subheader("📋 سجل البيانات التفصيلي المهني للآبار")
st.markdown("يمكنك استخدام الجدول أدناه للبحث عن أي بئر، ترتيب البيانات، أو استخراج التقارير:")

# عرض الجدول بطريقة تفاعلية تسمح بالترتيب والبحث والتحميل كـ Excel
st.dataframe(filtered_df, use_container_width=True)

