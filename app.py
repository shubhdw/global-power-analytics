import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import plugins

# 1. Page Configuration
st.set_page_config(page_title="Global Power Analytics", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('global_power_plant_database.csv', low_memory=False)
    # Ensure capacity is numeric for the graph
    df['capacity_mw'] = pd.to_numeric(df['capacity_mw'], errors='coerce')
    return df.dropna(subset=['latitude', 'longitude', 'capacity_mw'])

df = load_data()

# 2. Sidebar - Branding & Controls
st.sidebar.title("🌐 Energy Dashboard")
st.sidebar.markdown("---")

countries = sorted(df['country_long'].unique())
selected_country = st.sidebar.selectbox("Choose a Country", countries, index=countries.index("India"))

# Fuel Filter
available_fuels = sorted(df[df['country_long'] == selected_country]['primary_fuel'].unique())
selected_fuels = st.sidebar.multiselect("Filter Fuel Types", available_fuels, default=available_fuels)

# --- DATA PROCESSING ---
region_df = df[(df['country_long'] == selected_country) & (df['primary_fuel'].isin(selected_fuels))]

# Re-adding the Graph Functionality
st.sidebar.markdown("### Capacity by Fuel (MW)")
if not region_df.empty:
    capacity_stats = region_df.groupby('primary_fuel')['capacity_mw'].sum().sort_values(ascending=False)
    st.sidebar.bar_chart(capacity_stats) # This is the graph you wanted back!
else:
    st.sidebar.warning("No data for selected filters.")

# 3. Top Metrics (KPIs)
st.title(f"Energy Infrastructure: {selected_country}")
k1, k2, k3 = st.columns(3)

if not region_df.empty:
    total_mw = region_df['capacity_mw'].sum()
    k1.metric("Total Capacity", f"{total_mw:,.0f} MW")
    k2.metric("Plant Count", f"{len(region_df):,}")
    k3.metric("Main Source", capacity_stats.index[0])

# 4. Map Initialization
avg_lat, avg_lon = region_df['latitude'].mean(), region_df['longitude'].mean()
m = folium.Map(location=[avg_lat, avg_lon], zoom_start=5, tiles=None)

# Professional Basemaps
folium.TileLayer('openstreetmap', name='Street Map').add_to(m)
folium.TileLayer('CartoDB dark_matter', name='Dark Mode').add_to(m)
folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite Hybrid').add_to(m)

# Markers
colors = {'Nuclear': 'purple', 'Coal': 'black', 'Hydro': 'blue', 'Solar': 'orange', 'Gas': 'red', 'Wind': 'green'}

for fuel in selected_fuels:
    group = folium.FeatureGroup(name=fuel)
    data = region_df[region_df['primary_fuel'] == fuel]
    for _, row in data.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=6,
            popup=f"<b>{row['name']}</b><br>Capacity: {row['capacity_mw']} MW",
            color=colors.get(fuel, 'gray'),
            fill=True, fill_opacity=0.7
        ).add_to(group)
    group.add_to(m)

# 5. Legend & Controls
legend_items = "".join([f'<div><i class="fa fa-circle" style="color:{colors.get(f, "gray")}"></i> {f}</div>' for f in selected_fuels])
legend_html = f'''
     <div style="position: fixed; bottom: 50px; left: 50px; width: 140px; z-index:9999; font-size:14px;
     background-color:white; opacity: 0.9; padding: 10px; border:2px solid grey; border-radius:5px;">
     <b>Legend</b>{legend_items}</div>
     '''
m.get_root().html.add_child(folium.Element(legend_html))
folium.LayerControl(collapsed=False).add_to(m)
m.add_child(plugins.MiniMap(toggle_display=True))

# 6. Final Layout Display
st_folium(m, width=None, use_container_width=True, height=650)

# Raw Data Export
with st.expander("View & Download Raw Data"):
    st.dataframe(region_df.sort_values('capacity_mw', ascending=False), use_container_width=True)
    csv = region_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name=f"{selected_country}_data.csv")

# Credits
st.markdown("---")
col_a, col_b = st.columns(2)

with col_b:
    st.markdown(
        '<div style="text-align: right;">'
        '<a href="https://www.linkedin.com/in/shubham-wankhede-8b2b55a9/">'
        'Connect on LinkedIn 🔗</a></div>', 
        unsafe_allow_html=True)
with col_a:
    st.caption("⚠️ **Copyright:** © 2025 Shubham Wankhede | TISS, Mumbai")
    st.caption("📂 **Data Source:** World Resources Institute (WRI)")
    


