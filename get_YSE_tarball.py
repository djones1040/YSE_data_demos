import sys
import os
import tarfile

def get_tarball(tgzfile,outdir):

    if not os.path.exists(outdir):
        os.makedirs(my_output_dir)

    suffix2searchstring={
        'fits':'\d\.fits$',
        'wt.fits':'\d\.wt\.fits$',
        'mask.fits':'\d\.mask\.fits$'}

    tarDocument = tarfile.open(tgzfile)
    for item in tarDocument:
        for suffix in ['fits','wt.fits','mask.fits']:
            if re.search(suffix2searchstring[suffix],item.name):
                tarDocument.extract(item,outdir)

if __name__ == "__main__":
    import pdb; pdb.set_trace()
    get_tarball(sys.argv[1],sys.argv[2])
