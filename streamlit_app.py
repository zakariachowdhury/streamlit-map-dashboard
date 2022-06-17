# Data Source: https://public.tableau.com/app/profile/federal.trade.commission/viz/FraudandIDTheftMaps/AllReportsbyState
# US State Boundaries: https://public.opendatasoft.com/explore/dataset/us-state-boundaries/export/

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium
import folium

APP_TITLE = 'Fraud and Identity Theft Report'
APP_SUB_TITLE = 'Data Source: Federal Trade Comission'

def filter_data(df, year, quarter):
    return df[(df['Year'] == year) & (df['Quarter'] == quarter)]

def display_time_filters(df):
    year_list = list(df['Year'].unique())
    year_list.sort()
    year = st.sidebar.selectbox('Year', year_list, len(year_list)-1)
    quarter = st.sidebar.radio('Quarter', [1, 2, 3, 4])
    st.header(f'{year} Q{quarter}')
    return year, quarter

def display_state_filter(df, state_name=None):
    state_list = [''] + list(df['State Name'].unique())
    state_list.sort()
    state_name = st.sidebar.selectbox('State', state_list, state_list.index(state_name) if state_name and state_name in state_list else 0)
    return state_name

def display_report_type_filter(df, report_type=None):
    report_type_list = ['Fraud', 'Other']
    report_type = st.sidebar.selectbox('Report Type', report_type_list, report_type_list.index(report_type) if report_type else 0)
    return report_type

def display_map(df, year, quarter):
    df = filter_data(df, year, quarter)

    m = folium.Map(location=[38, -96.5], zoom_start=4, scrollWheelZoom=False, tiles=None)
    folium.TileLayer('CartoDB positron', control=False).add_to(m)
    choropleth = folium.Choropleth(
        geo_data='data/us-state-boundaries.geojson',
        name='United States',
        data=df,
        columns=['State Name', 'Fixed State F&O'],
        key_on='feature.properties.name',
        line_opacity=0.8,
        highlight=True
    )
    choropleth.geojson.add_to(m)

    df_indexed = df.set_index('State Name')
    for state in choropleth.geojson.data['features']:
        state_name = state['properties']['name']        
        state['properties']['population'] = 'Population: ' + '{:,}'.format(df_indexed.loc[state_name, 'State Pop'][0]) if state_name in list(df_indexed.index) else ''
        state['properties']['per_100k_reports'] = 'Reports/100K Population: ' + str(round(df_indexed.loc[state_name, 'Reports per 100K-F&O together'][0])) if state_name in list(df_indexed.index) else ''

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['name', 'population', 'per_100k_reports'], labels=False)
    )
    f = st_folium(m, width=700, height=450)

    state_name = None
    if f['last_active_drawing']:
        state_name = f['last_active_drawing']['properties']['name']

    return state_name

def display_top_categories(df, year, quarter):
    column_category = 'Category'
    column_total_reports = 'Total Reports by Category'

    df = filter_data(df, year, quarter)
    df = df[[column_category, column_total_reports]]
    df.drop_duplicates(inplace=True)    
    df = df.sort_values(column_total_reports)

    fig = px.bar(df, y=column_category, x=column_total_reports, orientation='h')
    st.plotly_chart(fig, use_container_width=True)

def display_fraud_facts(df, year, quarter, state_name, report_type, field, title, string_format='{:,}', is_median=False):
    df = filter_data(df, year, quarter)
    df = df[df['Report Type'] == report_type]
    if state_name:
        df = df[df['State Name'] == state_name]
    df.drop_duplicates(inplace=True)
    if is_median:
        total = df[field].sum() / len(df[field]) if len(df) else 0
    else:
        total = df[field].sum()
    st.metric(title, string_format.format(round(total)))

def main():
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)

    df_continental = pd.read_csv('data/AxS-Continental_Full Data_data.csv')
    df_fraud = pd.read_csv('data/AxS-Fraud Box_Full Data_data.csv')
    df_median = pd.read_csv('data/AxS-Median Box_Full Data_data.csv')
    df_loss = pd.read_csv('data/AxS-Losses Box_Full Data_data.csv')

    year, quarter = display_time_filters(df_continental)
    selected_state = display_map(df_continental, year, quarter)
    state_name = display_state_filter(df_continental, selected_state)
    report_type = display_report_type_filter(df_fraud)

    st.subheader(f'{state_name} {report_type} Facts')

    col1, col2, col3 = st.columns(3)
    with col1:
        display_fraud_facts(df_fraud, year, quarter, state_name, report_type, 'State Fraud/Other Count', f'# of {report_type} Reports')
    with col2:    
        display_fraud_facts(df_median, year, quarter, state_name, report_type, 'Overall Median Losses Qtr', 'Median $ Loss', string_format='${:,}', is_median=True)
    with col3:
        display_fraud_facts(df_loss, year, quarter, state_name, report_type, 'Total Losses', 'Total $ Loss', string_format='${:,}')

if __name__ == "__main__":
    main()