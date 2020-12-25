import streamlit as st
import folium
from streamlit_folium import folium_static
import geopandas as gpd
from PIL import Image
import random

import petrmodel

# import pydeck as pdk
# st.pydeck_chart(pdk.Deck(
#     map_style='mapbox://styles/mapbox/streets-v11',
#     initial_view_state=pdk.ViewState(latitude=37.76, longitude=-122.4, zoom=3, pitch=50)
#     )
# )

MAPBOX_API_KEY = "pk.eyJ1IjoiYWd5c2FyIiwiYSI6ImNrajFwOTZ2OTJ4ZGgydm1ta2hqbHRsMWsifQ.jGWxcborp5nh8BgdXNe_pA"
TILESET_ID_STR = "streets-v11"
TILESIZE_PIXELS = "256"
MOSCOW_LOCATION = [37.6155600, 55.7522200]


def get_map(country_dest, country_now):
    prediction_polygon = world.loc[world['name'] == country_dest]['geometry'].values[0]
    prediction_center = prediction_polygon.centroid.coords[0]
    m = folium.Map(location=[prediction_center[1], prediction_center[0]], 
                   tiles=f"https://api.mapbox.com/styles/v1/mapbox/{TILESET_ID_STR}/tiles/{TILESIZE_PIXELS}/{{z}}/{{x}}/{{y}}@2x?access_token={MAPBOX_API_KEY}",
                   attr="Mapbox",
                   zoom_start=3)
    if prediction_polygon.geom_type == 'Polygon':
        all_points = []
        for point in prediction_polygon.exterior.coords:
            all_points.append((point[1], point[0]))
        folium.Polygon(locations=all_points, color='green').add_to(m)
    else:
        for polygon in prediction_polygon:
            all_points = []
            for point in polygon.exterior.coords:
                all_points.append((point[1], point[0]))
            folium.Polygon(locations=all_points, color='green').add_to(m)
    folium.Marker(
        location=[prediction_center[1], prediction_center[0]], tooltip=country_dest, icon=folium.Icon(color='green', icon='check'), 
    ).add_to(m)
    folium.Polygon(locations=all_points, color='green').add_to(m)
    cur_country_poly = world.loc[world['name'] == country_now]['geometry'].values[0]
    cur_country_center = cur_country_poly.centroid.coords[0] if country_now != 'Russia' else MOSCOW_LOCATION
    folium.PolyLine(
        locations=[(prediction_center[1], prediction_center[0]), (cur_country_center[1], cur_country_center[0])],
        popup="Let's fly with Petr!").add_to(m)
    folium.Marker(
        location=[cur_country_center[1], cur_country_center[0]], tooltip="Start", icon=folium.Icon(color='blue',icon='plane', prefix="fa"),
    ).add_to(m)
    return m


world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

st.sidebar.title("Fill the form or try your luck!")
# background-color: rgba(180, 180, 180, 0.6);
PAGE_BY_IMG = '''
<style>
body {
background-image: url("https://github.com/obemika/petr-travel/blob/main/petr_flies.gif?raw=true");
background-size: cover;
background-color: rgba(0,0,0,.9);
}
.big-font {
    font-size: 20px !important;
    font-family: monospace;
    font-weight: bold;
    text-align: center;
    background-color: rgba(230, 170, 80, 0.6);
    border: 2px solid black;
    border-radius: 2px;
    margin-top: -50px;
}
.aftermap-font {
    font-size: 20px !important;
    font-family: monospace;
    font-weight: bold;
    text-align: center;
    background-color: rgba(230, 170, 80, 0.6);
    border: 2px solid black;
    border-radius: 2px;
}
</style>
'''

st.markdown(PAGE_BY_IMG, unsafe_allow_html=True)
data = petrmodel.PetrModel.load_data("./Countries and Features.csv")

COUNTRIES = ['Russia']
for elem in data['Country']:
    COUNTRIES.append(elem)

COUNTRY_RIGHT_NOW = st.sidebar.selectbox('Where are you now?', COUNTRIES)
COUNTRIES_VISITED = st.sidebar.multiselect('Select the countries you visited', COUNTRIES)
FLIGHT_LENGTH = st.sidebar.slider("How long are you ready to fly (in hours)?", 3, 12)
SIGHTSEEING_ATT = st.sidebar.slider("""Your attitude to sightseeing: 1 - Definitely not, 10 - Can't live without sightseeing""", 1, 10)
EXOTIC_ATT = st.sidebar.slider("What about exotic countries? 1 - Not this time, 10 - YEEEAH!", 1, 10)
SEASONS = ["Winter", "Spring", "Summer", "Autumn"]
SEASONS_CHOSEN = st.sidebar.multiselect('Your favourite season(s)', SEASONS)
SEA = st.sidebar.radio('Access to the sea', ("Yes", "No"))
PET = st.sidebar.radio('Choose your totem pet', ("Cat", "Dog"))

left_column, right_column = st.sidebar.beta_columns(2)

submit_btn = left_column.button("Submit!", key="Submit_btn")
lucky_btn = right_column.button('I am lucky!', key="Lucky_btn")

if submit_btn:
    # Processing prediction
    model = petrmodel.PetrModel(dataset=data, world=world)
    query = [
        1 if SEA == "Yes" else 0,
        1 if "Winter" in SEASONS_CHOSEN else 0,
        1 if "Spring" in SEASONS_CHOSEN else 0,
        1 if "Summer" in SEASONS_CHOSEN else 0,
        1 if "Autumn" in SEASONS_CHOSEN else 0,
        SIGHTSEEING_ATT,
        1 if PET == "Dog" else 0,
        EXOTIC_ATT,
        FLIGHT_LENGTH
    ]
    top_1, others = model.predict(COUNTRY_RIGHT_NOW, COUNTRIES_VISITED, query)
    if top_1:
        advice = ""
        for i in range(len(others)):
            advice = advice + others[i]
            if i != (len(others) - 1):
                advice += ", "
        st.markdown('<p class="big-font">' + "The best country for your next visit: " + top_1 + '</p>', unsafe_allow_html=True)
        m = get_map(top_1, COUNTRY_RIGHT_NOW)
        folium_static(m)
        st.markdown('<p class="aftermap-font">' + "Also you can visit: " + advice + '</p>', unsafe_allow_html=True)
        image = Image.open("Aviasales.png")
        st.image(image, use_column_width=True)
        st.sidebar.success("Finished!")
    else:
        st.markdown('<p class="big-font">' + "Sorry, too few flight hours, no countries can be reached :(" + '</p>', unsafe_allow_html=True)
        image = Image.open("Aviasales.png")
        st.image(image, use_column_width=True)
        st.sidebar.success("Try more hours!")

elif lucky_btn:
    top_1 = random.choice(COUNTRIES)
    st.markdown('<p class="big-font">' + "The best country for your next visit: " + top_1 + '</p>', unsafe_allow_html=True)
    m = get_map(top_1, COUNTRY_RIGHT_NOW)
    folium_static(m)
    image = Image.open("Aviasales.png")
    st.image(image, use_column_width=True)
    st.sidebar.success("Well, gods of random made their choice!")
