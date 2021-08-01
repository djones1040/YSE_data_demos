import os
import numpy as np
import requests
from lxml import html
import re
from astropy.coordinates import SkyCoord
import astropy.units as u
import glob
import tarfile

### skycell ID function, from Armin
def getskycell(ra,dec):
    session = requests.Session()
    session.auth = ('ps1sc','skysurveys')
    skycellurl = 'http://pstamp.ipp.ifa.hawaii.edu/findskycell.php'
    Nx,Ny = 6279,6261
    
    # First login. Returns session cookie in response header. Even though status_code=401, it is ok
    page = session.post(skycellurl)
        
    info = {'ra': (None, str(ra)), 'dec': (None, str(dec))}

    page = session.post(skycellurl, files=info)
    if page.status_code!=200:
        raise RuntimeError('Could not get the webpage %s setting ra=%s and dec=%s, status message %s' % (skycellurl,ra,dec,page.text))

    tree = html.fromstring(page.text)
    skycells=[]
    Xs=[]
    Ys=[]
    for cell in tree.xpath("//td[text()='RINGS.V3']/following::td[1]"):
        skycells.append(re.sub('skycell\.','',cell.text_content()))
    for cell in tree.xpath("//td[text()='RINGS.V3']/following::td[2]"):
        Xs.append(float(cell.text_content()))
    for cell in tree.xpath("//td[text()='RINGS.V3']/following::td[3]"):
        Ys.append(float(cell.text_content()))

    if len(skycells)==1:
        best_i=0
    else:
        # get the best skycell: biggest distance to the border of the image
        best_i = None
        bestmindistance = 0.0
        for i in range(len(skycells)):
            mindistance = min(abs(Nx-Xs[i]),abs(0-Xs[i]),abs(Ny-Ys[i]),abs(0-Ys[i]))
            if mindistance>bestmindistance:
                best_i = i
                bestmindistance=mindistance

        if best_i==None: raise RuntimeError('BUG!!!')
        #print('best skycell:',skycells[best_i],Xs[best_i],Ys[best_i])

    return(skycells[best_i],Xs[best_i],Ys[best_i],len(skycells))

if __name__ == "__main__":

    # first get the skycell ID
    sc = SkyCoord('12:30:49.42338230','+12:23:28.0438581',unit=(u.hour,u.deg))
    skycell = getskycell(sc.ra.deg,sc.dec.deg)[0]
    print(f"skycell: {skycell}")

    tgzfiles = glob.glob(f"/lustre/hpc/storage/dark/YSE/raw_YSE_data/*.warp.*/*{float(skycell)}.tgz")

    my_output_dir = 'output'
    if not os.path.exists(my_output_dir):
        os.makedirs(my_output_dir)
    
    suffix2searchstring={
        'fits':'\d\.fits$',
        'wt.fits':'\d\.wt\.fits$',
        'mask.fits':'\d\.mask\.fits$'}

    # just get the first 10 for now
    for t in tgzfiles[0:10]:
        tarDocument = tarfile.open(t)
        for item in tarDocument:
            for suffix in ['fits','wt.fits','mask.fits']:
                if re.search(suffix2searchstring[suffix],item.name):
                    tarDocument.extract(item,my_output_dir)

    # let's use a batch script to get the next 10
    batch_header = """#!/bin/bash
#SBATCH -o yse_data_copy.%i.stdout
#SBATCH -e yse_data_copy.%i.stderr
#SBATCH -p dark
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 1
#SBATCH --ntasks-per-core 1
#SBATCH --mem-per-cpu 2000
#SBATCH --time=06:00:00"""

    for i,t in enumerate(tgzfiles[10:11]):
        print(t)
        # I put the above lines into a short script that can be run at
        # the command line
        batch_cmd = f"python get_YSE_tarball.py {t} {my_output_dir}"

        with open(f'batch_data_job_{i}.sh','w') as fout:
            print(batch_header%(i,i),file=fout)
            print(batch_cmd,file=fout)
            print('',file=fout)
        os.system(f'sbatch batch_data_job_{i}.sh')
