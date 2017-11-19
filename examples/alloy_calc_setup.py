#!/usr/bin/env python
from catscreen import dft, util
from catscreen.dict_definitions import *

lat_dict = {'Pt':3.93,'Pd': 3.963,'Ni':3.526}

all_ads = { 'CH3':'ontop'}

#Calc Parameters#
host = 'Pt'
cov = [3, 3]
facet = 111
lat_const = lat_dict[host]

#SP parameters
deltaz = 2
conc = range(1, 5)
layer = 3 
natoms = n_layer['{}-{}x{}'.format(111,cov[0],cov[1])] # no. of atoms per layer

# Job submission
q1 = 'smp'
q2 = 'smp'
cluster = 'h2p'

# Reference data
slab_args = {'host':host, 'cov': cov, 'lat':lat_const, 'fac':facet}
slabdir = 'slab/{1}x{2}/{0}-slab-{1}x{2}'.format(host,cov[0],cov[1])
geom = dft.ref()

for ads, site in all_ads.iteritems():
    nads = ads_dict[ads][1] # number of atoms in adsorbate
    ads_args = dict(slab_args)
    ads_args.update({'ads':ads, 'site':site})
    adsdir = '{2}_BE/{3}/{0}x{1}/{4}-slab-{0}x{0}-{2}-{3}'.format(cov[0],
                                                                  cov[1],ads,
                                                                  site,host)
    ads_esp = geom.ret_esp(adsdir,ads=ads,cov=cov[1])
    if cov[1] == 2:
        inert_sites = range(0,4)
        active_sites = range(0,4)
    else:
        inert_sites, active_sites = util.unique_esp(ads_esp,nads,natoms,facet,layer)
    sites = [inert_sites, active_sites]

    sp = dft.alloy(slabdir = slabdir, adsdir = adsdir)
    sp.setup(calctype='slab',deltaz = deltaz,sites=sites,layer=layer,
             conc_values=conc,q=q1,clus=cluster,**slab_args)
    sp = dft.alloy(slabdir = slabdir, adsdir = adsdir)
    sp.setup(calctype='ads',deltaz=deltaz, sites=sites, layer=layer,
             conc_values=conc,q=q2,clus=cluster,**ads_args)
