#!/usr/bin/env python
from catscreen import dft, archiver

#Calc Parameters#
lat_dict = {'Pt':3.93,'Pd': 3.963,'Ni':3.526}

host = 'Pt'
cov = [2, 2]
lat_const = lat_dict[host]
facet = 111
root = None
ads_dict = {'CH3':'ontop'}

# Slab setup
slab_args = {'host':host, 'cov': cov, 'lat':lat_const, 'fac':facet, 
             'ads':None,'site':None,'root':root}
slabdir = 'slab/{1}x{2}/{0}-slab-{1}x{2}'.format(host,cov[0],cov[1])
geom = dft.ref()
en = geom.read_energy(slabdir)
archiver.add_refdata(energy=en,**slab_args)

# Ads setup
for ads, site in ads_dict.iteritems():
    adsdir = '{2}_BE/{3}/{0}x{1}/{4}-slab-{0}x{0}-{2}-{3}'.format(cov[0],
                                                                  cov[1],ads,
                                                                  site,host)
    ads_args = dict(slab_args)
    ads_args.update({'ads':ads, 'site':site})
    en = geom.read_energy(adsdir)
    archiver.add_refdata(energy=en,**ads_args)
