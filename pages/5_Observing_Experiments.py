import streamlit as st
import mlflow
import webbrowser

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
import base64 

def center_image(image_path, caption=None):
    # Create a container with custom CSS to center the image
    st.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="{image_path}" alt="Image" style="width: auto; height: auto; max-width: 50%; max-height: 50%;" />'
        f'</div>',
        unsafe_allow_html=True
    )

#Page code

# Use the glob module to get a list of files in the current directory
file_list = glob("cases/*")

# Use st.sidebar.selectbox to create a selectbox in the sidebar
selected_file = st.selectbox("List of Possible Experiments", file_list)

if selected_file:

    short = selected_file.split('/')[-1]    

    df = mlflow.search_runs(experiment_names=[short])

    if df.empty:

        st.text('This experiment does not yet have an Mlflow experiment linked to it \n \
Try another one')

    else:

        exp_id = df.iloc[0].experiment_id

        st.dataframe(data=df)        

        if st.button("Show Results"):

            image_path = "/Users/iatake/Dropbox (CMCC)/Work/MEDSLIK-II and Pyslick/Medslik-II_Streamlit/MDK_Streamlit/example3.gif"
            caption = ""

            # Center the image on the Streamlit app
            """### Test 1 Output Example"""
            file_ = open(image_path, "rb")
            contents = file_.read()
            data_url = base64.b64encode(contents).decode("utf-8")
            file_.close()

            st.markdown(
                f'<img src="data:image/gif;base64,{data_url}" alt="test1 example">',
                unsafe_allow_html=True,
)
            
        


    
    


                            



