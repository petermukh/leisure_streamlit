import math
import streamlit as st
from PIL import Image
import pandas as pd
import geopandas as gpd
import folium
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import folium_static
import shortest_path
import networkx as nx
import osmnx as ox

import warnings
warnings.filterwarnings('ignore')

# run streamlit
with st.echo(code_location='below'):
    st.markdown("<h1 style='text-align: center; color: black;'>Досуг в городе Москва</h1>", unsafe_allow_html=True)
    img = Image.open('logo.jpg')

    _, col2, _ = st.columns([1,6,1])

    with col2:
        st.image(img)

    # Загружаем датасет по местам досуга и данные по округам
    #-----------------------------------------------------------------------------------------------------
    st.subheader('Датасет по местам досуга в Москве.')
    df = pd.read_csv('./data/combined_rating_counts.csv')
    df.drop(columns = 'Unnamed: 0', axis = 1, inplace= True)
    
    df_msc = pd.read_csv('./data/moscow_areas.csv')
    df_msc.drop(columns = 'Unnamed: 0', axis = 1, inplace= True)

    if st.checkbox('Показать исходный датасет'):
        count = st.slider('Кол-во строк', 1, df.shape[0], df.shape[0])
        st.write(df[:count+1])
    
    if st.checkbox('Показать данные по округам Москвы'):
        st.write(df_msc)
    #-----------------------------------------------------------------------------------------------------
    
    # Виды досуга
    leisure = {
        'autodrome_close' : 'закрытый автодром',
        'autodrome_open' : 'открытый автодром',
        'pool_close' : 'закрытый бассейн',
        'pool_open' : 'открытый бассейн',
        'tennis' : 'теннис',
        'train_gym' : 'тренировочный зал',
        'sport_gym' : 'спортивный зал',
        'aquapark' : 'аквапарк',
    }
    st.write('Датасет включает себя следующие типы досугов:')
    for key, val in leisure.items():
        st.markdown("- " + val + ';')


    # Анализ данных
    st.subheader('Анализ данных.')
    #-----------------------------------------------------------------------------------------------------
    # Количество мест по каждому типу
    df['Type'] = df['Type'].map(leisure)
    type_counts = df['Type'].value_counts()
    fig_count_type = px.bar(type_counts, x=type_counts.index, y=type_counts.values, labels={'x': 'Тип', 'y': 'Кол-во'})
    fig_count_type.update_layout(title='Кол-во мест досуга по каждому типу')
    st.plotly_chart(fig_count_type)
    #-----------------------------------------------------------------------------------------------------
    
   #-----------------------------------------------------------------------------------------------------
    # Количество мест в зависимости от округа
    count_by_area = df.groupby('AdmArea')['Name'].count().reset_index()
    fig_bar_area = px.bar(count_by_area, x='AdmArea', y='Name', labels={'AdmArea': 'AdmArea', 'Name': 'Count'}, title='Count of Places by AdmArea')
    fig_bar_area.update_layout(title='Кол-во мест досуга по округу города')
    st.plotly_chart(fig_bar_area)
    #-----------------------------------------------------------------------------------------------------

    #-----------------------------------------------------------------------------------------------------
    # График box-plot для рейтинга и типа досуга 
    df_ratings = df[df['Rating'] != -1]
    fig_bp = px.box(df_ratings, x='Type', y='Rating', labels={'x': 'Type', 'y': 'Average Rating'})
    fig_bp.update_layout(title='Рейтинг мест по типу досуга')
    st.plotly_chart(fig_bp)
    #-----------------------------------------------------------------------------------------------------

    #-----------------------------------------------------------------------------------------------------
    # Точечный график мест отдыха с рейтингом и количеством отзывов
    fig_scatter = px.scatter(df_ratings, x='Rating', y='NumReviews', color='Type', hover_data=['Name', 'Address'])
    fig_scatter.update_layout(title='Точечный график мест отдыха с рейтингом и количеством отзывов')
    st.plotly_chart(fig_scatter)
    #-----------------------------------------------------------------------------------------------------

    #-----------------------------------------------------------------------------------------------------
    # Отношение кол-ва мест к площади округа + отображение спарсенной таблицы
    st.write("Расчет отношения кол-ва мест к площади округов.")
    if st.button('Выполнить'):
        msc_stats_table = df_msc[["Округ", "Площадь км²1.07.2012"]]
        msc_stats_table['Площадь км²1.07.2012'] = msc_stats_table['Площадь км²1.07.2012'].str.replace(',', '.')
        msc_stats_table['Отношение'] = df.groupby(['AdmArea'])['AdmArea'].count().tolist() / msc_stats_table['Площадь км²1.07.2012'].astype(float)
        st.write(msc_stats_table)
        
        fig_ratio = px.bar(msc_stats_table, x='Округ', y='Отношение', title='Отношение кол-ва мест к площади округа')
        st.plotly_chart(fig_ratio)
    #-----------------------------------------------------------------------------------------------------


    # подгружаем данные по округам с сайта
    # https://gis-lab.info/qa/moscow-atd.html#.D0.90.D0.B4.D0.BC.D0.B8.D0.BD.D0.B8.D1.81.D1.82.D1.80.D0.B0.D1.82.D0.B8.D0.B2.D0.BD.D1.8B.D0.B5_.D0.BE.D0.BA.D1.80.D1.83.D0.B3.D0.B0
    #-----------------------------------------------------------------------------------------------------
    geo_data = gpd.read_file('./data/ao.geojson')
    geo_data.insert(geo_data.shape[1], 'centroid', geo_data.geometry.centroid)

    st.markdown("<h5 style='text-align: center;'>Карта Москвы с округами.</h5>", unsafe_allow_html=True)   
    plot_areas = folium.Map(location=[55.751999, 37.617734], zoom_start=12)

    # отрисуем зоны округов желтым цветом
    for _, row in geo_data.iterrows():
        sim_geo = gpd.GeoSeries(row['geometry']).simplify(tolerance=0.001)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {'fillColor': 'yellow'})
        folium.Popup(row['NAME']).add_to(geo_j)
        geo_j.add_to(plot_areas)
    
    # отрисуем метки в центре округов
    for _, row in geo_data.iterrows():
        lon = row['centroid'].x
        lat = row['centroid'].y
        folium.Marker(location=[lat, lon], popup='Округ: {}'.format(row['NAME'])).add_to(plot_areas)
    folium_static(plot_areas)
    #-----------------------------------------------------------------------------------------------------

    # Отрисовка исходных данных на карте Москвы
    #-----------------------------------------------------------------------------------------------------
    st.markdown("<h5 style='text-align: center;'>Отоброжение мест досуга на карте с краткой информацией.</h5>", unsafe_allow_html=True)

    show_count = st.slider('Кол-во данных для отображение', 1, math.ceil(df.shape[0] / 2), 250)
    places = []
    df_temp = df.head(show_count)

    for i, row in df_temp.iterrows():
        places.append({
            'index': i,
            'coordinates': [row['Latitude'], row['Longitude']],
            'location': row['Address'],
            'name': row['Name'],
            'type': row['Type'],
            'mon': row['понедельник'],
            'tue': row['вторник'],
            'wed': row['среда'],
            'thu': row['четверг'],
            'fri': row['пятница'],
            'sat': row['суббота'],
            'sun': row['воскресенье'],
        })

    marker_coordinates = [[float(x) for x in place['coordinates']] for place in places]

    # берем координаты города Москва https://www.latlong.net/place/moscow-russia-431.html
    plot_places = folium.Map(location=[55.751244, 37.618423], zoom_start=12)

    information_box = """
        <div style="width: 300px;">
        <dl>
        <dt>Тип:</dt><dd>{type}</dd>
        <dt>Название:</dt><dd>{name}</dd>
        <dt>Адрес:</dt><dd>{location}</dd>
        <dt>Режим работы.</dt>
        <dt>Пн:</dt><dd>{mon}</dd>
        <dt>Вт:</dt><dd>{tue}</dd>
        <dt>Ср:</dt><dd>{wed}</dd>
        <dt>Чт:</dt><dd>{thu}</dd>
        <dt>Пт:</dt><dd>{fri}</dd>
        <dt>Сб:</dt><dd>{sat}</dd>
        <dt>Вск:</dt><dd>{sun}</dd>
        </dl>
        </div>
    """

    locations_info = [information_box.format(**place) for place in places]

    for i, place in enumerate(places):
        folium.Marker(
            location=marker_coordinates[i],
            popup=locations_info[i],
            tooltip=place['name']
        ).add_to(plot_places)

    folium_static(plot_places)
    #-----------------------------------------------------------------------------------------------------


    #-----------------------------------------------------------------------------------------------------
    st.markdown("<h5 style='text-align: center;'>Три ближайших места досуга.</h5>", unsafe_allow_html=True)
    place_types = tuple(leisure.values())
    select_type = st.selectbox(
            'Выберите тип досуга',
            place_types,
            index=2
        )
    street = st.text_input('Введите улицу', placeholder='Малая Молчановка')
    house_number = st.text_input('Введите номер дома', placeholder='4')
    
    df_by_type = df[df['Type'] == select_type]
    if 'start_lat' not in st.session_state and 'start_lon' not in st.session_state:
        st.session_state.start_lat = 0.0
        st.session_state.start_lon = 0.0
    if 'nearest_places' not in st.session_state:
        st.session_state.nearest_places = []

    if st.button('Поиск'):
        places_result = []
        
        st.session_state.start_lat, st.session_state.start_lon = shortest_path.get_long_lat_by_text(street, house_number)

        names = list(df_by_type['Name'])
        addresses = list(df_by_type['Address'])
        lats = list(df_by_type['Latitude'])
        longs = list(df_by_type['Longitude'])

        places = zip(names, addresses, lats, longs)
        start_loc = [st.session_state.start_lat, st.session_state.start_lon]
        result = shortest_path.get_nearest(start_loc, list(places))
        st.session_state['nearest_places'] = result

    selected_place = st.selectbox('Выберите место.', options=[opt.strip() for opt in st.session_state.nearest_places]) 

    if st.button('Нарисовать путь'):
        ox.config(log_console=True, use_cache=True)
        start = (st.session_state.start_lat, st.session_state.start_lon)
        choose_name, choose_address = selected_place.split('. ')[0], selected_place.split('. ')[1]
        end = (df[(df['Name'] == choose_name) & (df['Address'] == choose_address)]['Latitude'].values[0], 
            df[(df['Name'] == choose_name) & (df['Address'] == choose_address)]['Longitude'].values[0])

        G, m = shortest_path.plot_path(start, end)
        st.write('Если расстояние между точками слишком большое, то путь может до конца не прорисоваться.')
        folium_static(m)
    #-----------------------------------------------------------------------------------------------------


