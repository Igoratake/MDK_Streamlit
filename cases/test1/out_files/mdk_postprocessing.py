import os
import pdb
import glob
import re

xp_name = input('type the name of the experiment youd like to postprocess (e.g.: "paria_case"): ')
host_folder = '/scratch/work/lab/'
xp_folder = host_folder + xp_name

ss = glob.glob(xp_folder + '/out_files/MD*')

sim_folder = ss[0] 
bnc_folder = xp_folder + '/bnc_files/'

# get sim _ info
with open(sim_folder + '/config1.txt') as f:
    lines = f.readlines()

# sim_length
ss = lines[1]
print ss
rr = re.search('=(.*)\n',ss)
sim_length = int(lines[1][11:15])
# sim_day
ss = lines[5]
print ss
rr = re.search('=(.*)\n',ss)
dd = int(rr.group(1))
# sim_month
ss = lines[6]
print ss
rr = re.search('=(.*)\n',ss)
mm = int(rr.group(1))
# sim_year
ss = lines[7]
print ss
rr = re.search('=(.*)\n',ss)
yy = rr.group(1)
yy = '20' + yy
# sim_hora
ss = lines[8]
print ss
rr = re.search('=(.*)\n',ss)
hh = int(rr.group(1))
# sim_minute
ss = lines[9]
print ss
rr = re.search('=(.*)\n',ss)
mmin = int(rr.group(1))


# generate oil_track maps
os.system("LC_CTYPE=C && LANG=C sed 's#INPFOLD#" + sim_folder + "#' /scratch/work/scripts/templates/oil_track_witoil.py > " + xp_folder + "/oil_track_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPYY/" + yy + "/' " + xp_folder + "/oil_track_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPMM/" + str(mm) + "/' " + xp_folder + "/oil_track_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPDD/" + str(dd) + "/' " + xp_folder + "/oil_track_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPHH/" + str(hh) + "/' " + xp_folder + "/oil_track_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/DURA/" + str(sim_length) + "/' " + xp_folder + "/oil_track_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/MUNIT/" + '%02d' % (mmin) + "/' " + xp_folder + "/oil_track_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's#BATFOLD#" + bnc_folder + "#' " + xp_folder + "/oil_track_custom.py")
os.system('python ' + xp_folder + '/oil_track_custom.py')

# generate oil_beached maps
os.system("LC_CTYPE=C && LANG=C sed 's#INPFOLD#" + sim_folder + "#' /scratch/work/scripts/templates/oil_beached_witoil.py > " + xp_folder + "/oil_beached_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPYY/" + yy + "/' " + xp_folder + "/oil_beached_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPMM/" + str(mm) + "/' " + xp_folder + "/oil_beached_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPDD/" + str(dd) + "/' " + xp_folder + "/oil_beached_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPHH/" + str(hh) + "/' " + xp_folder + "/oil_beached_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/DURA/" + str(sim_length) + "/' " + xp_folder + "/oil_beached_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/MUNIT/" + '%02d' % (mmin) + "/' " + xp_folder + "/oil_beached_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's#BATFOLD#" + bnc_folder + "#' " + xp_folder + "/oil_beached_custom.py")
os.system('python ' + xp_folder + '/oil_beached_custom.py')

# generate center of mass file
os.system("LC_CTYPE=C && LANG=C sed 's#INPFOLD#" + sim_folder + "#' /scratch/work/scripts/templates/co_mass_witoil.py > " + xp_folder + "/co_mass_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPYY/" + yy + "/' " + xp_folder + "/co_mass_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPMM/" + str(mm) + "/' " + xp_folder + "/co_mass_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPDD/" + str(dd) + "/' " + xp_folder + "/co_mass_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/INPHH/" + str(hh) + "/' " + xp_folder + "/co_mass_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/MUNIT/" + '%02d' % (mmin) + "/' " + xp_folder + "/co_mass_custom.py")
os.system("LC_CTYPE=C && LANG=C sed -i 's/DURA/" + str(sim_length) + "/' " + xp_folder + "/co_mass_custom.py")
os.system('python ' + xp_folder + '/co_mass_custom.py')
