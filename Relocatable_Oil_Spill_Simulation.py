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
    caption = ""

    # Center the image on the Streamlit app
    center_image(image_path, caption)

    image_path2 = "https://www.imt-atlantique.fr/sites/default/files/projetderecherche/Edito%20Model-Lab.png"
    caption2 = ""

    # Center the image on the Streamlit app
    center_image(image_path2, caption2)

    st.write("# Relocatable oil spill simulation with SURF and Medslik-II")

    st.markdown(
        """
        This application allows any user to launch any oil spill simulations on an area of interest by using environmental fields provided by a high resolution from SURF Framework.
        """
    )   
        

if __name__ == "__main__":
    main()

