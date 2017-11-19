#!/usr/bin/env python
import sqlite3 as lite
from archiver import sql_file
from catscreen import dft,util
from dict_definitions import * 
import sys

'''
Writer modules in this file.
1. Calc DFT and Alc BE of all alloys
2. Write data in csv format
'''

def fetchDB(queryargs, nullstr, jobtype, calctype):
    con = lite.connect(sql_file)
    cur = con.cursor()
    if jobtype == 'ref':
        if calctype == 'slab':
            query = tuple(queryargs[:-2])
            qs = """SELECT * from refdata WHERE 
                 host = ? AND facet = ? AND cov = ? AND
                 root {} AND ads is null AND 
                 bindsite is null""".format(nullstr)
        elif calctype == 'ads':
            query = queryargs
            qs = """SELECT * from refdata WHERE 
                 host = ? AND facet = ? AND cov = ? 
                 AND root {} AND ads is ? AND 
                 bindsite is ? """.format(nullstr)

    elif jobtype == 'alloy':
        if calctype == 'slab':
            query = queryargs[:-2]
            qs = """SELECT * from alloydata WHERE 
                 host = ? AND facet = ? AND cov = ? 
                 AND root {} AND alloytype = ? AND 
                 ads is null AND bindsite is null""".format(nullstr)
        elif calctype == 'ads':
            query = queryargs
            qs = """SELECT * from alloydata WHERE 
                 host = ? AND facet = ? AND cov = ? 
                 AND root {} AND alloytype = ? AND 
                 ads = ? AND bindsite = ? """.format(nullstr)
    try:
        cur.execute(qs,query)
#        cur.execute("select * from refdata where host = ? and facet=? and cov=? and root = ? and ads is null and bindsite is null",query)
        rows = cur.fetchall()
    except lite.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
    return rows

def calc_BEref(**args):
    '''
    Return BE of ref slab and ads 
    '''
    if args['root'] == None:
        nullstr = 'is null'
        queryargs = [args['host'],args['fac'],args['cov'],
                    args['ads'],args['site']]
    else:
        nullstr = '= ?'
        queryargs = [args['host'],args['fac'],args['cov'],
                    args['root'],args['ads'],args['site']]

    slab_data = fetchDB(queryargs, nullstr, jobtype='ref', calctype='slab')
    slab_energy = slab_data[0][-2]

    ads_data = fetchDB(queryargs, nullstr, jobtype='ref', calctype='ads')
    ads_energy = ads_data[0][-2]

    if len(slab_data) > 1 or len(ads_data) > 1:
        sys.exit("Non unique record found for refBE")

    mol_energy = e_mol_dict[args['ads']] 
    refBE = slab_energy + mol_energy - ads_energy
    return refBE

def calc_BEalloy(natoms, layer, **args):
    '''
    Return BE of alloy slab and ads
    '''
    nf = open('./data/{}-{}-{}-{}.csv'.format(args['host'],args['cov'],
                                             args['ads'],args['site']),'w')
    nf.write('molid,deltaz,inert,active,delBE_dft,delBE_alc\n')
    refBE = calc_BEref(**args)

    geom = dft.ref()
    slabdir = 'slab/{1}/{0}-slab-{1}'.format(args['host'],args['cov'])
    adsdir = '{0}_BE/{1}/{2}/{3}-slab-{2}-{0}-{1}'.format(args['ads'],
                                                          args['site'],
                                                          args['cov'],
                                                          args['host'])
    slab_esp = geom.ret_esp(slabdir,cov=int(args['cov'][-1]))
    ads_esp = geom.ret_esp(adsdir,ads=args['ads'],cov=int(args['cov'][-1]))
    delta_esp = []
    for i in range(len(ads_esp)):
        delta_esp.append(float(ads_esp[i]) - float(slab_esp[i]))

    mol_energy = e_mol_dict[args['ads']] 
    if args['root'] == None:
        nullstr = 'is null'
        queryargs = [args['host'],args['fac'],args['cov'],
                     args['alloytype'],args['ads'],args['site']]
    else:
        nullstr = '= ?'
        queryargs = [args['host'],args['fac'],args['cov'],args['root'],
                     args['alloytype'],args['ads'],args['site']]
    ads_data = fetchDB(queryargs, nullstr, jobtype='alloy', calctype='ads')
    
    for alloyentry in ads_data:
        alloyid = alloyentry[5]
        ads_energy = alloyentry[-3]
        con = lite.connect(sql_file)
        cur = con.cursor()
        query = [alloyid,args['cov'],args['fac']]

        try:
            cur.execute('SELECT * from alloydata WHERE '
                        'alloy = ? and ads is NULL and cov=? and '
                        'facet = ? ',(query))
            rows = cur.fetchall()
        except lite.Error, e:
            print "Error %s:" % e.args[0]
            sys.exit(1)

        print alloyid #, len(rows), rows 
        if len(rows) ==1:
            slab_energy = rows[0][-3]
            spBE =  slab_energy + mol_energy - ads_energy

            inert_sol = alloyid.split('-')[0].split('_')[-1]
            deltaz = ele_dict[inert_sol] - ele_dict[args['host']]
            isite = [int(i) for i in alloyentry[7].split('.')]
            asite = [int(i) for i in alloyentry[8].split('.')]
            aesp = util.esp_layer(delta_esp, natoms, layer)
            iesp = util.esp_layer(delta_esp, natoms, 1)
            alcder = calc_alcder(isite,asite,iesp,aesp,deltaz)   
            istr = ':'.join([str(s) for s in isite])
            astr = ':'.join([str(s) for s in asite])
            nf.write('{},{},{},{},{},{}\n'.format(alloyid, abs(deltaz), istr,
                                                  astr, spBE - refBE, alcder))
        else:
            print 'Non unique alloy found'
def calc_alcder(isite,asite,iesp,aesp,deltaz):
    '''
    Return alcder of alloy slab and ads
    '''
    alcder = 0
    for i in isite:
        alcder = alcder + iesp[i]*deltaz
    for i in asite:
        alcder = alcder + aesp[i]*-deltaz
    return alcder

def write_data(natoms,layer,**args):
    calc_BEalloy(natoms,layer,**args)



