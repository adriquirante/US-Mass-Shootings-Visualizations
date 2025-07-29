import streamlit as st
import altair as alt
import pandas as pd
from vega_datasets import data as vega


def get_Vis():

    #-----------------------Loading Data-------------------------------------------
    data = pd.read_csv('MassShootings_Cleaned.csv')

    #-----------------------Data for Q1 and Q3-------------------------------------
    dataQ1 = data.copy()

    # Region population to millions
    dataQ1['Region population'] = (dataQ1['Region population'] /1000000).round(2)
    dataQ1['Region population'] = dataQ1['Region population'].astype(str) + 'M'

    # State population to millions
    dataQ1['Population state'] = (dataQ1['Population state']/1000000).round(2)
    dataQ1['Population state'] = dataQ1['Population state'].astype(str) + 'M'

    # County population thousands
    dataQ1['Population county'] = (dataQ1['Population county']/1000).round(2)
    dataQ1['Population county'] = dataQ1['Population county'].astype(str) + 'K'

    # Data map
    data_map = dataQ1.copy()


    # Creating new columns: total incidents per Region, County and State
    data_map['Total Incidents Region'] = data_map.groupby('Region')['Incidents'].transform('sum')
    data_map['Total Incidents State'] = data_map.groupby('State')['Incidents'].transform('sum')
    data_map['Total Incidents County'] = data_map.groupby(['City Or County', 'FIPS county'])['Incidents'].transform('sum')

    data_map = data_map[['State', 'FIPS state',  'Population state',
                        'City Or County', 'FIPS county', 'Population county',
                        'Region', 'Region population',
                        'Total Incidents Region', 'Total Incidents State', 'Total Incidents County']]

    data_map = data_map.drop_duplicates() # Shows only one row per county

    # Data Regions
    data_region = dataQ1.groupby(['Region', 'Incident Date']).agg({
        'Incidents' : 'sum',
        'Region population': 'first'
    }).reset_index()

    data_region['Year'] = data_region['Incident Date'].str[:4]


    # Data States
    data_state = dataQ1.groupby(['Incident Date', 'Region', 'State', 'FIPS state']).agg({
        'Incidents' : 'sum',
        'Population state': 'first'
    }).reset_index()

    data_state['Year'] = data_state['Incident Date'].str[:4]

    # Data counties
    data_counties = data_map.copy()

    #------------------------Data for Q2---------------------------------------

    dataQ2 = data[['Incident Date', 'State', 'FIPS state', 'Incidents', 'Region', 'Region population']]
    dataQ2['Year'] = dataQ2['Incident Date'].str[:4]

    #data region Q2
    region_incidents = dataQ2.groupby(['Year', 'Region']).agg(
        Incidents=('Incidents', 'sum'),
        Population_Region=('Region population', 'first')
    ).reset_index()

    region_incidents['Incident rate'] = region_incidents['Incidents'] / region_incidents['Population_Region']*1000000
    region_incidents = region_incidents[['Year', 'Region', 'Incident rate']]

    #-----------------------Flters------------------------------------
    #Dropwdown Filters
    input_dropdownInitial = alt.binding_select(options=[2019, 2020, 2021, 2022, 2023], name='Select Initial Year: ')
    year_selectionInitial = alt.param(value=2019, bind=input_dropdownInitial)

    input_dropdownFinal = alt.binding_select(options=[2019, 2020, 2021, 2022, 2023], name='Select Final Year: ')
    year_selectionFinal = alt.param(value=2023, bind=input_dropdownFinal)

    #Slder Filter
    slider_min = alt.binding_range(min=2019, max=2023, step=1, name='Select Initial Year: ')
    op_min = alt.param(value=2019, bind=slider_min)

    slider_max = alt.binding_range(min=2019, max=2023, step=1, name='Select Final Year: ')
    op_max = alt.param(value=2023, bind=slider_max)

    # ---------------Regions Map Visualization------------------------
    map = alt.topo_feature(vega.us_10m.url, feature='states')

    region_colors = {
        'West': '#CA596D',
        'Southeast': '#4F4488',
        'Northeast': '#44AA99',
        'Midwest': '#DDCC77',
        'Southwest': '#88CCEE',
    }
    color_domain = list(region_colors.keys())
    color_range = list(region_colors.values())

    usChart = alt.Chart(map).mark_geoshape(
        fill='#fce2e1',
        stroke='black',
        strokeWidth=0.25
    ).properties(
        width=500,
        height=300
    ).project('albersUsa')

    select_region = alt.selection_point(fields=['Region'])

    colors = alt.Chart(map).mark_geoshape(stroke='black', strokeWidth=0.25).transform_lookup(
        lookup='id',
        from_=alt.LookupData(data_map, 'FIPS state', ['Region', 'Region population', 'Total Incidents Region'])
    ).transform_filter(
        alt.datum.Region != None
    ).encode(
        alt.Color('Region:N', scale = alt.Scale(domain=color_domain, range=color_range)),
        opacity=alt.condition(select_region, alt.value(1.0), alt.value(0.2), tooltip='Region:N'),
        tooltip=[
            alt.Tooltip('Region:N', title='Region'),
            alt.Tooltip('Region population:N', title='Population'),
            alt.Tooltip('Total Incidents Region:Q', title='Total incidents')
        ]
    ).add_params(select_region).project(
        type='albersUsa'
    ).properties(
        title='US map',
        width=500,
        height=300)

    # -------------------Region Q1 statitistics visualization-----------------------------

    lineChart_Regions = alt.Chart(data_region).mark_line().encode(
        x=alt.X('Incident Date:N', title='Period', axis=alt.Axis(labelAngle=0, labelAlign='center')),
        y=alt.Y('Incidents:Q', title='Incidents'),
        color=alt.Color('Region:N', legend=alt.Legend(title='Region')),
        opacity=alt.condition(select_region, alt.value(1.0), alt.value(0.2), tooltip='Region:N')
    ).transform_filter(
        (alt.datum.Year >= op_min) & (alt.datum.Year <= op_max)
    ).add_params(select_region, op_min, op_max).properties(
        width=500,
        height=300,
        title = 'Evolution of mass shootings in US across regions'
    )

    pointChart_Regions = alt.Chart(data_region).mark_circle(color='#3b9f9f').encode(
        x='Incident Date:N',
        y='Incidents:Q',
        color='Region:N',
        opacity=alt.condition(select_region, alt.value(1.0), alt.value(0.2), tooltip='Region:N')
    ).encode(
        tooltip=[
            alt.Tooltip('Incidents:Q', title='Incidents'),
            alt.Tooltip('Region:N', title='Region'),
            alt.Tooltip('Region population:N', title='Population')
        ]
    ).transform_filter(
        (alt.datum.Year >= op_min) & (alt.datum.Year <= op_max)
    ).add_params(select_region, op_min, op_max).properties(
        width=500,
        height=300,
        title = 'Evolution of mass shootings in US across regions'
    )

    #---------------Region Q2 Statistics----------------------------

    # Filtering the data: only shows data from 2019 and selected year

    lines = alt.Chart(region_incidents).mark_line().encode(
        x=alt.X('Year:O', title='Year', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Incident rate:Q', title='Incidents per 1M inhabitants', scale=alt.Scale(domain=[0.2, 3.2])),
        color=alt.Color('Region:N', legend=alt.Legend(title="Region")),
        opacity=alt.condition(select_region, alt.value(1.0), alt.value(0.2), tooltip='Region:N')
    ).add_params(select_region, op_max).transform_filter(
        (select_region)
    ).transform_filter(
        (alt.datum.Year == '2019') | ((alt.datum.Year >= op_max) & (alt.datum.Year <= op_max))
    ).properties(
        width=500,
        height=300,
        title='Changes in mass shooting rates (per million) in the US over the years'
    )

    points = alt.Chart(region_incidents).mark_point(size=100, filled = True).encode(
        x='Year:O',
        y='Incident rate:Q',
        color='Region:N',
        opacity=alt.condition(select_region, alt.value(1.0), alt.value(0.2), tooltip='Region:N'),
        tooltip=[
            alt.Tooltip('Region:N', title='Region'),
            alt.Tooltip('Year:O', title='Year'),
            alt.Tooltip('Incident rate:Q', title='Incident Rate', format=".2f")
        ]
    ).transform_filter(
        (select_region)
    ).transform_filter(
        (alt.datum.Year == '2019') | ((alt.datum.Year >= op_max) & (alt.datum.Year <= op_max))
    ).add_params(select_region, op_max).properties(
        width=500,
        height=300,
        title='Changes in mass shooting rates (per million) in the US over the years'
    )

    #---------------States Map Visualization-----------------


    select_state = alt.selection_point(fields=['State'])

    filteredMap_States = alt.Chart(map).mark_geoshape(
        stroke='black',
        strokeWidth=0.25
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(data_map, 'FIPS state', ['Region', 'State', 'Population state', 'Total Incidents State'])
    ).transform_filter(
        (select_region) & (alt.datum.Region != None) & (alt.datum.State != None)
    ).encode(
        alt.Color('Region:N', legend=None),
        opacity=alt.condition(select_state, alt.value(1.0), alt.value(0.2), tooltip='State:N'),
        tooltip=[
            alt.Tooltip('State:N', title='State'),
            alt.Tooltip('Population state:N', title='Population'),
            alt.Tooltip('Total Incidents State:Q', title='Total incidents')
        ]
    ).add_params(select_state, select_region).project(
        type='albersUsa'
    ).properties(
        width=500,
        height=300,
        title='States of the Selected Region'
    )


    #------------------States Statistics--------------------------

    lineChart_States = alt.Chart(data_state).mark_line().encode(
        x=alt.X('Incident Date:N', title='Period', axis=alt.Axis(labelAngle=0, labelAlign='center')),
        y=alt.Y('Incidents:Q', title='Incidents'),
        color=alt.Color('Region:N', legend=alt.Legend(title='Region')),
        opacity=alt.condition(select_state, alt.value(1.0), alt.value(0.1), tooltip='Region:N'),
        detail = 'State:N'
    ).transform_filter(
    (select_region) &  (alt.datum.Year >= op_min) & (alt.datum.Year <= op_max)
    ).encode(
    tooltip=[
        alt.Tooltip('State:N', title='State'),
        alt.Tooltip('Population state:N', title='Population')
    ]
    ).add_params(select_state, select_region, op_min, op_max).properties(
        width=500,
        height=300,
        title = 'Evolution of mass shootings in US across states'
    )

    pointChart_States = alt.Chart(data_state).mark_circle(color='#3b9f9f').encode(
        x='Incident Date:N',
        y='Incidents:Q',
        color='Region:N',
        opacity=alt.condition(select_state, alt.value(1.0), alt.value(0.1), tooltip='Region:N')
    ).transform_filter(
    (select_region) &  (alt.datum.Year >= op_min) & (alt.datum.Year <= op_max) 
    ).encode(
        tooltip=[
            alt.Tooltip('Incidents:Q', title='Incidents'),
            alt.Tooltip('State:N', title='State'),
            alt.Tooltip('Population state:N', title='Population')
        ]
    ).add_params(select_state, select_region, op_min, op_max).properties(
        width=500,
        height=300,
        title = 'Evolution of mass shootings in US across states'
    )

    #------------------Counties Map changing opacity if there's no incident-------------------
    map_Counties = alt.topo_feature(vega.us_10m.url, feature='counties')

    filteredMap_Counties = alt.Chart(map_Counties).mark_geoshape(
        stroke='black',
        strokeWidth=0.25
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(data_map, 'FIPS county', ['City Or County', 'Region', 'State', 'Population county', 'Total Incidents County'])
    ).transform_filter(
        (select_state) & (select_region) & (alt.datum.Region != None) & (alt.datum.State != None) & (alt.datum['City Or County'] != None)
    ).encode(
        alt.Color('Region:N', scale = alt.Scale(domain=color_domain, range=color_range)),
        opacity = alt.condition(alt.datum['Total Incidents County'] != 0, alt.value(1.0), alt.value(0.2), tooltip='City Or County:N'),
        tooltip=[
            alt.Tooltip('City Or County:N', title='County'),
            alt.Tooltip('Population county:N', title='Population'),
            alt.Tooltip('Total Incidents County:Q', title='Total incidents')
        ]
    ).add_params(select_state, select_region).project(
        type='albersUsa'
    ).properties(
        width=500,
        height=300,
        title='Counties of the selected State and Region'
    )

    #-------------------Counties Statistics-------------------------------
    barChart_Counties = alt.Chart(data_counties).mark_bar().encode(
        alt.X('Total Incidents County:Q', title= 'Incidents'),
        alt.Y('City Or County:N', sort='-x', title = 'Counties'),
        alt.Color('Region:N')
    ).transform_filter(
    (select_region) & (select_state) & (alt.datum['Total Incidents County'] != 0)
    ).transform_window(
        rank='rank(Total Incidents County)',
        sort=[alt.SortField('Total Incidents County', order='descending')]
    ).transform_filter(
        alt.datum.rank < 8
    ).properties(
        width=500,
        height=300,
        title='Counties with most mass shootings in US (2019-2023)'
    ).add_params(select_state, select_region)

    left_spacer = alt.Chart().mark_text().encode().properties(width=250)  # Ajusta el ancho del espaciador izquierdo
    #-------------------Visualizations------------------------------------
    regionVIS = (left_spacer | (usChart + colors)) & ((lineChart_Regions + pointChart_Regions) | (lines + points)) 
    top_chart = usChart + colors
    Q2VIS = (usChart + colors) & (lines + points)
    statesVIS = filteredMap_States & (lineChart_States + pointChart_States)
    countiesVIS = filteredMap_Counties & barChart_Counties

    Vis = regionVIS | statesVIS | countiesVIS
    return Vis


st.set_page_config(layout="wide")





st.markdown(
    "<h1 style='text-align: right;'>  Final Streamlit Visualization VI Project 2</h1>", 
    unsafe_allow_html=True)


col1, col2, col3 = st.columns([1, 1, 1.8])

with col3:
    st.write("By Guillem Garrido Bonastre and Adrian Quirante González")








VIS = get_Vis()
st.altair_chart(VIS)