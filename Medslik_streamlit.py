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
   

def main():
    
    st.set_page_config(
    page_title="MedSlik-II interface",
    page_icon="👋",
    )

    image_path = "https://www.cmcc.it/wp-content/themes/pisces-child/assets/img/logo_footer_CMCC.png"
    caption = "CMCC FOUNDATION"

    # Center the image on the Streamlit app
    center_image(image_path, caption)

    st.write("# Medslik Custom Simulation App")

    st.markdown(
        """
        The oil spill model code MEDSLIK-II (De Dominicis et. al 2013, Part 1 and Part 2), based on its precursor oil spill model MEDSLIK (Lardner and Zodiatis 1998; Lardner et al. 2006; Zodiatis et al. 2008) is a freely available community model and can be downloaded from this website. It is designed to be used to predict the transport and weathering of an oil spill, using a lagrangian representation of the oil slick.
        """
    )   
        

if __name__ == "__main__":
    main()

