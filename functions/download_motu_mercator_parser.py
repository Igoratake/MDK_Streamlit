import motuclient
import argparse
import os
import subprocess
import datetime

class MotuOptions:
    def __init__(self, attrs: dict):
        super(MotuOptions, self).__setattr__("attrs", attrs)

    def __setattr__(self, k, v):
        self.attrs[k] = v

    def __getattr__(self, k):
        try:
            return self.attrs[k]
        except KeyError:
            return None  


def download(date_start, date_end, 
                    depth_min, depth_max,
                    lat_min, lon_min,lat_max,lon_max,
                    service_id,product_id,var,
                    output_path,output_name,
                    user,psd):


    data_request_options_dict_manual = {
        "service_id": service_id,
        "product_id": product_id,
        "date_min": date_start,
        "date_max": date_end,
        "longitude_min": lon_min,
        "longitude_max": lon_max,
        "latitude_min": lat_min,
        "latitude_max": lat_max,
        "depth_min": depth_min,
        "depth_max": depth_max,
        "variable": var,
        "motu": "https://nrt.cmems-du.eu/motu-web/Motu",
        "out_dir": output_path,
        "out_name": output_name,
        "auth_mode": "cas",
        "user": user,
        "pwd": psd
        }
    
    return data_request_options_dict_manual

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Download Mercator")

    # Define command-line arguments
    parser.add_argument('date_start', type=str, help='Start date of the simulation')
    parser.add_argument('date_end', type=str, help='End date of the simulation')
    parser.add_argument('depth_min', type=float, help='Minimum depth value')
    parser.add_argument('depth_max', type=float, help='Maximum depth value')
    parser.add_argument('lat_min', type=float, help='Mininum Latitude value')
    parser.add_argument('lon_min', type=float, help='Minimum Longitude value')
    parser.add_argument('lat_max', type=float, help='Maximum Latitude value')
    parser.add_argument('lon_max', type=float, help='Maximum Longitude value')
    parser.add_argument('down', type=str, help='Indication of global or local data')
    parser.add_argument('output_path', type=str, default='.', help='Output path (default: current directory)')
    parser.add_argument('user', type=str, default='.', help='Copernicus Username')
    parser.add_argument('psd', type=str, default='.', help='Copernicus Password')

    parser

    # Parse the command-line arguments
    args = parser.parse_args()

    outputs = []

    if args.down == 'global':
        loc = 'glo'
        service_id = "GLOBAL_ANALYSISFORECAST_PHY_001_024-TDS"
        ref = '0.083deg'
        temp = 'thetao'

    else:
        loc = 'med'
        service_id = "MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS"
        ref = '4.2km'
        temp = 'tem'
        

    for var in ['curr','temp']:

        if var == 'curr':
            product_id = f"cmems_mod_{loc}_phy-cur_anfc_{ref}_P1D-m"
            varr = ['uo','vo']
        elif var == 'temp':
            product_id = f"cmems_mod_{loc}_phy-{temp}_anfc_{ref}_P1D-m"
            varr = ['thetao']
        
        outputname = f'{var}_tempo.nc'
        outputs.append(outputname)

        request = download(args.date_start, args.date_end, 
                        args.depth_min, args.depth_max, 
                        args.lat_min, args.lon_min, args.lat_max, args.lon_max, 
                        service_id,product_id,varr,
                        args.output_path,outputname,
                        args.user,args.psd)

        motuclient.motu_api.execute_request(MotuOptions(request))

#   real start date
    real_date = datetime.datetime.strptime(args.date_start[0:10],'%Y-%m-%d')
    real_date = real_date + datetime.timedelta(days=1) 

    subprocess.run(f'cdo merge {args.output_path}{outputs[0]} {args.output_path}{outputs[1]}\
                    {args.output_path}CMEMS_{loc}_{real_date.year}{real_date.month}{real_date.day}_raw.nc',shell=True,check=True)

    subprocess.run(f'rm {args.output_path}{outputs[0]} {args.output_path}{outputs[1]}',shell=True,check=True)

