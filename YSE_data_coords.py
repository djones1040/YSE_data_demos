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
        for suffix in ['fits','wt.fits','mask.fits']:
            if re.search(suffix2searchstring[suffix],item.name):
                tarDocument.extract(item,my_output_dir)
