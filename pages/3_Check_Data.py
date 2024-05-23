import streamlit as st

#geo libs
import folium
import xarray as xr
import geojsoncontour
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import Point
from folium.plugins import HeatMap
from streamlit_folium import st_folium,folium_static

#numerical and plotting libs
import numpy as np
import matplotlib.pyplot as plt
import plotly.figure_factory as ff

#system libs
import os
import sys
import time
import datetime
import subprocess
import threading
from glob import glob 

def collect_depth():
    
    st.write(int(st.session_state.depth))

def analyze_map(ds,dep):

    rec = ds.sel(depth=dep,method='nearest')

    st.header('Component u')
    col5,col6,col7 = st.columns(3)
    
    col5.metric('Minimum Velocity',f'{np.nanmin(rec.uo.values):.2f} m/s')
    col6.metric('Maximum Velocity',f'{np.nanmax(rec.uo.values):.2f} m/s')
    col7.metric('Average Velocity',f'{np.nanmean(rec.uo.values):.2f} m/s')

    st.header('Component v')
    col8,col9,col10 = st.columns(3)
    
    col8.metric('Minimum Velocity',f'{np.nanmin(rec.vo.values):.2f} m/s')
    col9.metric('Maximum Velocity',f'{np.nanmax(rec.vo.values):.2f} m/s')
    col10.metric('Average Velocity',f'{np.nanmean(rec.vo.values):.2f} m/s')

    st.header('Field Characteristics')
    col11,col12,col13 = st.columns(3)
    rec['vel'] = (rec.uo**2+rec.vo**2)**0.5
    meandir = (180+180/np.pi*np.arctan2(np.nanmean(rec.vo),np.nanmean(rec.uo)))

    col11.metric('Average Velocity',f'{np.nanmean(rec.vel.values):.2f} m/s')
    col12.metric('Average Direction',f'{meandir:.2f} Deg')
    col13.metric('Average Temperature',f'{np.nanmean(rec.thetao.values):.2f} Celsius')

def plot_gridlines_on_map(nc_file):
    # Read the NetCDF data using xarray
    ds = xr.open_dataset(nc_file)

    # Extract latitude, longitude, and grid values
    lats = ds.lat.values
    lons = ds.lon.values
    grid_values = ds.isel(time=0,depth=0).vo.values

    # Create a Streamlit map
    st.write("NetCDF Data on Map:")

    map = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=4)

    figure = plt.figure()
    ax = figure.add_subplot(111)
    contour = ax.contour(lons,lats,grid_values)

    geojson = geojsoncontour.contour_to_geojson(contour=contour,ndigits=3,unit='m')

    c = folium.Choropleth(geo_data=geojson)

    c.geojson.add_to(map)

    # Show the map on the Streamlit app
    folium_static(map)    
    

def center_image(image_path, caption=None):
    # Create a container with custom CSS to center the image
    st.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="{image_path}" alt="Image" style="width: auto; height: auto; max-width: 50%; max-height: 50%;" />'
        f'</div>',
        unsafe_allow_html=True
    )

     # Optionally display the caption below the image
    if caption:
        st.caption(caption)


#Page code
    
st.title("Data available")

# Use the glob module to get a list of files in the current directory
file_list = glob("data/MERCATOR/*mdk.nc")

# Use st.sidebar.selectbox to create a selectbox in the sidebar
selected_file = st.selectbox("Select a file", file_list)

# Display the selected file
st.write(f"Selected File: {selected_file}")

# Button to analyze data
#    if st.button("Analyze file data"):

if selected_file:

    ds = xr.open_dataset(selected_file)

    col1,col2,col3,col4 = st.columns(4)

    col1.metric('Minimum Latitude',f'{np.nanmin(ds.lat)} Deg')
    col2.metric('Maximum Latitude',f'{np.nanmax(ds.lat)} Deg')
    col3.metric('Minimum Longitude',f'{np.nanmin(ds.lon)} Deg')
    col4.metric('Maximum Longitude',f'{np.nanmax(ds.lon)} Deg')

    plot_gridlines_on_map(selected_file)        

    depths = ds.depth.values

    #        st.selectbox("Select a depth", options=depths, on_change='collect_depth',key='depth')
    option = st.selectbox("Select a depth", options=depths)

    st.write('Depth :',option)
    st.session_state['depth'] = int(option)

    if st.session_state.depth != 0:

        analyze_map(ds,st.session_state.depth)
          


