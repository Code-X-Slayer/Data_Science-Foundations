import os
import streamlit as st
import requests
import time
from dotenv import load_dotenv

load_dotenv()

def flatten_dict(d, parent_key="", sep="__"):
    items = []
    for k, v in d.items():
        new_key = parent_key+sep+k if parent_key else k
        if isinstance(v,dict):
            items.extend(flatten_dict(v,new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)

base_url = "http://api.weatherapi.com/v1"
curr_url = "/current.json"
forecast_url = "/forecast.json"
search_url = "/search.json"
key = os.getenv("WEATHER_API_KEY")
if not key:
    st.error("API key not found! Please set WEATHER_API_KEY in .env or environment variables.")

st.set_page_config(page_title="Weather", layout="centered")
st.title("🌤️ Weather Data")
st.info("""
For best results, please enter the exact location name or latitude,longitude coordinates.  
Partial or ambiguous names may return nearby or unrelated locations due to the API's fuzzy search.  
Using precise coordinates or full names ensures more accurate weather data.
""")

user_location = st.text_input("Enter location:")
st.markdown("""
You can enter:  
- current ip (.)
- city name (e.g. Paris)  
- latitude and longitude (e.g. 48.8567,2.3508)  
- US ZIP code (e.g. 10001)  
- UK postcode (e.g. SW1)  
- Canada postal code (e.g. G2J)  
- METAR code (e.g. metar:EGLL)  
- airport code (e.g. iata:DXB)  
- IP lookup (e.g. auto:ip)  
- IP address (e.g. 100.0.0.1)
""")

forecast_days = st.slider("Select forecast days (1-2)",1,2,value=1)

button1, button2 = st.columns(2)

@st.cache_data
def validate_location(location):
    if location.strip()=="":
        return []
    url = base_url + search_url
    params = {'key':key, 'q':location}
    r = requests.get(url,params=params)
    if r.status_code==200:
        return r.json()
    else:
        return []

def get_current_weather(location):
    if ',' in location:
        lat, lon = location.split(',')
        st.write(f"Fetching current weather for: {lat}N, {lon}E")
    else:
        st.write(f"Fetching current weather for: {location}")
    url = base_url + curr_url
    params = {'key':key, 'q':location}
    time.sleep(1.2)
    r = requests.get(url,params=params)
    if r.status_code == 200:
        data = r.json()
        # st.write("Current Weather raw data: ", data)
        return flatten_dict(r.json())
    else:
        st.error(f"Error in fetching current weather data: {r.status_code}")
        return None

@st.cache_data
def get_forecast_weather(location,days):
    if ',' in location:
        lat, lon = location.split(',')
        st.write(f"Fetching forecast weather for: {lat}N, {lon}E")
    else:
        st.write(f"Fetching forecast weather for: {location}")
    url = base_url + forecast_url
    params = {'key':key, 'q':location, 'days':days+1}
    time.sleep(1.2)
    r = requests.get(url,params=params)
    if r.status_code == 200:
        return r.json()
    else:
        st.error(f"Error in fetching forecast weather data: {r.status_code}")
        return None

query_location = user_location.strip() if user_location.strip()!='.' else "auto:ip"


if 'selected_location_index' not in st.session_state:
    st.session_state.selected_location_index = 0
if 'validated_location' not in st.session_state:
    st.session_state.validated_location = None

locations = []

if query_location not in ("","auto:ip"):
    locations = validate_location(query_location)

if not locations and query_location not in ("","auto:ip"):
    st.warning("No locations found, please enter a valid location details.")
    st.session_state.validated_location = None
    
elif len(locations)==1:
    loc = locations[0]
    st.session_state.validated_location = f"{loc['lat']},{loc['lon']}"
    
elif len(locations)>1:
    options = ["-- Select a location --"] + [f"{loc['name']}, {loc['region']}, {loc['country']}" for loc in locations]
    if 'selected_location_index' not in st.session_state:
        st.session_state.selected_location_index = 0
    selection= st.selectbox(
        "Multiple locations found, please select:",
        options,
        index=st.session_state.selected_location_index,
        key="location_select_box"
    )
    if selection != "-- Select a location --":
        st.session_state.selected_location_index = options.index(selection)
        selected_loc = locations[st.session_state.selected_location_index-1]
        st.session_state.validated_location = f"{selected_loc['lat']},{selected_loc['lon']}"
    else:
        st.session_state.validated_location = None

elif query_location in ("", "auto:ip"):
    st.session_state.validated_location = query_location

if button1.button("Get Weather"):
    st.session_state.pop('current_weather', None)
    st.session_state.pop('forecast_data', None)
    if not st.session_state.validated_location:
        st.warning("Please enter a location before fetching current weather.")
    else:
        with st.spinner("Loading current weather..."):
            data = get_current_weather(st.session_state.validated_location)
        if data:   
            st.session_state.current_weather = data
        else:
            st.warning("No weather data available for this location.")

if button2.button("Get Forecast"):
    st.session_state.pop('current_weather', None)
    st.session_state.pop('forecast_data', None)
    if not st.session_state.validated_location:
        st.warning("Please enter a valid location before fetching forecast weather.")
    else:
        with st.spinner("Loading forecast weather..."):
            fc_data = get_forecast_weather(st.session_state.validated_location, forecast_days)
        if fc_data and 'forecast' in fc_data:
            st.session_state.forecast_data = fc_data
        else:
            st.warning("No forecast data found.")

if 'current_weather' not in st.session_state and 'forecast_data' not in st.session_state:
    st.info("Enter a location and click 'Get Weather' or 'Get Forecast' to see weather information.")

if 'current_weather' in st.session_state:
    data = st.session_state.current_weather
    try:
        st.markdown(f"### 📍 Location: {data['location__name']}, {data['location__region']}, {data['location__country']}")
        st.markdown(f"### ⏰ Local Time: {data['location__localtime']}")
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            icon_url = "https:" + data['current__condition__icon']
            st.image(icon_url, width=64)
        with col2:
            st.markdown(f"#### Condition: {data['current__condition__text']}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Temperature (°C)", f"{data['current__temp_c']}°C")
        col2.metric("Temperature (°F)", f"{data['current__temp_f']}°F")
        col3.metric("Humidity (%)", f"{data['current__humidity']}%")
        col1, _ = st.columns([1, 2])
        col1.metric("Wind Speed (kph)", f"{data['current__wind_kph']} kph")
    except Exception as e:
        st.warning(f"Current weather data unavailable or incomplete. Error: {str(e)}")
    
if 'forecast_data' in st.session_state:
    fc_data = st.session_state.forecast_data

    loc = fc_data.get('location', {})
    st.markdown(f"### 📍 Location: {loc.get('name', '')}, {loc.get('region', '')}, {loc.get('country', '')}")
    st.markdown(f"### ⏰ Local Time: {loc.get('localtime', '')}")
    st.markdown("---")

    forecast_days_list = fc_data['forecast']['forecastday']
    for day in forecast_days_list:
        date = day.get('date', '')
        day_info = day.get('day', {})
        condition = day_info.get('condition', {})

        st.markdown(f"### Forecast for {date}")
        col1, col2 = st.columns([1, 3])
        with col1:
            icon_url = "https:" + condition.get('icon', '')
            if icon_url.strip() != "https:":
                st.image(icon_url, width=64)
        with col2:
            st.markdown(f"Condition: {condition.get('text', 'N/A')}")
            st.markdown(f"Max Temp: {day_info.get('maxtemp_c', 'N/A')}°C")
            st.markdown(f"Min Temp: {day_info.get('mintemp_c', 'N/A')}°C")
            
        st.markdown("---")