"""
#;+ 
#; NAME:
#; lls_literature
#;   Ordered by publication date
#;    Version 1.0
#;
#; PURPOSE:
#;    Module for loading up literature data on Lyman Limit Systems
#;   29-Jun-2015 by JXP
#;-
#;------------------------------------------------------------------------------
"""

from __future__ import print_function, absolute_import, division, unicode_literals

import os, copy, sys, imp, glob
import numpy as np
import urllib2

from astropy import units as u
from astropy.io import ascii 

from linetools.lists.linelist import LineList
from linetools.spectralline import AbsLine

from xastropy.atomic import ionization as xai
from xastropy.igm.abs_sys.lls_utils import LLSSystem
from xastropy.igm.abs_sys.ionclms import IonClms
from xastropy.igm.abs_sys import ionclms as xiai
from xastropy.obs import radec as xor 
from xastropy.xutils import xdebug as xdb

xa_path = imp.find_module('xastropy')[1]

#class LLSSystem(AbslineSystem):
#class LLS_Survey(Absline_Survey):

def zonak2004():
    '''Zoank, S. et al. 2004, ApJ, 2004, 606, 196
    PG1634+706
    HST+Keck spectra
    MgII, SiIV, SiIII from Table 2.  Summing Subsystems A (Model 2) and B
       Errors estimated by JXP (not reported)
       SiIII in A may be a model
       SiIV in B may be a model
    Total NHI from LL. Taken from Fig 3 caption.  
       Error estimated by JXP 
    Not all EWs in Table 1 included
    Adopting their M/H
    '''
    # Setup
    radec = xor.stod1('J163428.9897+703132.422') # SIMBAD
    lls = LLSSystem(name='PG1634+706_z1.041', RA=radec[0], Dec=radec[1], zem=1.337,
        zabs=1.0414, vlim=[-200., 30.]*u.km/u.s, NHI=17.23, MH=-1.4,
        sigNHI=np.array([0.15,0.15])) 
    # SubSystems
    lls.mk_subsys(2) 
    # Abundances
    adict = dict(MgII={'clm': log_sum([11.45,11.90,12.02,11.68]), 'sig_clm': 0.05, 'flg_clm': 1},
        SiIII={'clm': log_sum([12.5,12.5,12.8,12.7]), 'sig_clm': 0.25, 'flg_clm': 1},
        SiIV={'clm': log_sum([10.9,10.8,11.2,11.1]), 'sig_clm': 0.15, 'flg_clm': 1} )
    lls.subsys['A']._ionclms = IonClms(idict=adict)
    bdict = dict(SiIII={'clm': log_sum([11.8,12.8,12.4]), 'sig_clm': 0.15, 'flg_clm': 1},
        SiIV={'clm': log_sum([11.2,12.2,11.8]), 'sig_clm': 0.15, 'flg_clm': 1} )
    lls.subsys['B']._ionclms = IonClms(idict=bdict)
    # Total
    lls._ionclms = lls.subsys['A']._ionclms.sum(lls.subsys['B']._ionclms)
    lls.Refs.append('Zon04')
    # Return
    return lls

def jenkins2005():
    '''Jenkins, E. et al. 2005, ApJ, 2005, 623, 767
    PHL 1811
    HST/STIS, FUSE
    Metals parsed from Table 1
      OI taken from text
      Had to input error on columns by hand (JXP)
    Total NHI from Lyman series. see Fig 3
    M/H from O/H
    '''
    # Grab ASCII file from ApJ
    tab_fil = xa_path+"/data/LLS/jenkins2005.tb1.ascii"
    chk_fil = glob.glob(tab_fil)
    if len(chk_fil) > 0:
        tab_fil = chk_fil[0]
    else:
        url = 'http://iopscience.iop.org/0004-637X/623/2/767/fulltext/61520.tb1.txt'
        print('LLSSurvey: Grabbing table file from {:s}'.format(url))
        f = urllib2.urlopen(url)
        with open(tab_fil, "wb") as code:
            code.write(f.read())
    # Setup
    radec = xor.stod1('J215501.5152-092224.688') # SIMBAD
    lls = LLSSystem(name='PHL1811_z0.081', RA=radec[0], Dec=radec[1], zem=0.192,
        zabs=0.080923, vlim=[-100., 100.]*u.km/u.s, NHI=17.98, MH=-0.19,
        sigNHI=np.array([0.05,0.05])) 

    # AbsLines
    ism = LineList('ISM')
    Nsig = {'C IV': 0.4, 'N II': 0.4, 'Si II': 0.05, 'Si IV': 0.25, 
        'S II': 0.2, 'Fe II': 0.12, 'H I': 0.05, 'S III': 0.06}

    # Parse Table
    with open(tab_fil,'r') as f:
        flines = f.readlines()
    ion_dict = {}
    for iline in flines:
        iline = iline.strip()
        if (len(iline) == 0): 
            continue
        # Split on tabs
        isplit = iline.split('\t')
        # Offset?
        ioff = 0
        if isplit[0][0] in ['1','2']:
            ioff = -1
        # Catch bad lines
        if (isplit[1+ioff][0:6] in ['1442.0','1443.7','1120.9']): # Skip goofy CII line and CII*
            continue
        if len(isplit[2+ioff]) == 0: 
            continue
        # Ion
        if (len(isplit[0].strip()) > 0) & (isplit[0][0] not in ['1','2']):
            ionc = isplit[0].strip()
            try:
                Zion = xai.name_ion(ionc)
            except KeyError:
                xdb.set_trace()
        # Generate the Line
        try:
            newline = AbsLine(float(isplit[2+ioff])*u.AA,linelist=ism, closest=True)
        except ValueError:
            xdb.set_trace()
        newline.attrib['z'] = lls.zabs
        # Spectrum
        newline.analy['datafile'] = 'STIS' if 'S' in isplit[1] else 'FUSE'
        # EW
        try:
            EWvals = isplit[4+ioff].split(' ')
        except IndexError:
            xdb.set_trace()
        newline.attrib['EW'] = float(EWvals[0])*u.AA/1e3
        newline.attrib['EWsig'] = float(EWvals[2])*u.AA/1e3
        newline.attrib['flgEW'] = 1
        if len(isplit) < (5+ioff+1):
            continue
        # Colm?
        #xdb.set_trace()
        if (len(isplit[5+ioff].strip()) > 0) & (isplit[5+ioff].strip() != '\\ldots'):
            if isplit[5+ioff][0] == '\\':
                ipos = isplit[5+ioff].find(' ')
                newline.attrib['N'] = float(isplit[5+ioff][ipos+1:])
                newline.attrib['flagN'] = 2
            elif isplit[5+ioff][0] == '<':
                ipos = 0
                newline.attrib['N'] = float(isplit[5+ioff][ipos+1:])
                newline.attrib['flagN'] = 3
            elif isplit[5+ioff][0] == '1':
                try:
                    newline.attrib['N'] = float(isplit[5+ioff][0:5])
                except ValueError:
                    xdb.set_trace()
                newline.attrib['flagN'] = 1
                try:
                    newline.attrib['Nsig'] = Nsig[ionc]
                except KeyError:
                    print('No error for {:s}'.format(ionc))
            else:
                raise ValueError('Bad character')
            # ion_dict
            ion_dict[ionc] = dict(clm=newline.attrib['N'], sig_clm=newline.attrib['Nsig'],
                flg_clm=newline.attrib['flagN'], Z=Zion[0], ion=Zion[1])  
        # Append
        lls.lines.append(newline)
    # Fix NI, OI
    ion_dict['O I']['clm'] = 14.47
    ion_dict['O I']['sig_clm'] = 0.05
    ion_dict['N I']['flg_clm'] = 3
    lls._ionclms = IonClms(idict=ion_dict)

    lls.Refs.append('Jen05')
    # Return
    return lls

def tripp2005():
    '''Tripp, T. et al. 2005, ApJ, 2005, 619, 714
    PG 1216+069 (LLS in Virgo)
    HST/STIS, FUSE
    Metal columns parsed from Tables 2 and 3
    Total NHI from damping wings
    M/H from O/H
    '''
    # Grab ASCII file from ApJ
    tab_fils = [xa_path+"/data/LLS/tripp2005.tb3.ascii", xa_path+"/data/LLS/tripp2005.tb2.ascii"]
    urls = ['http://iopscience.iop.org/0004-637X/619/2/714/fulltext/60797.tb3.txt',
        'http://iopscience.iop.org/0004-637X/619/2/714/fulltext/60797.tb2.txt']
    for jj,tab_fil in enumerate(tab_fils):
        chk_fil = glob.glob(tab_fil)
        if len(chk_fil) > 0:
            tab_fil = chk_fil[0]
        else:
            url = urls[jj]
            print('LLSSurvey: Grabbing table file from {:s}'.format(url))
            f = urllib2.urlopen(url)
            with open(tab_fil, "wb") as code:
                code.write(f.read())
    # Setup
    radec = xor.stod1('J121920.9320+063838.476') # SIMBAD
    lls = LLSSystem(name='PG1216+069_z0.006', RA=radec[0], Dec=radec[1], zem=0.3313,
        zabs=0.00632, vlim=[-100., 100.]*u.km/u.s, NHI=19.32, MH=-1.6,
        sigNHI=np.array([0.03,0.03])) 
    #lls.mk_subsys(2) 
 
    # Columns
    # Start with Table 3 (VPFIT)
    with open(tab_fils[0],'r') as f:
        flines3 = f.readlines()
    ion_dict = {}
    for iline in flines3:
        if (len(iline.strip()) == 0): 
            continue
        isplit = iline.split('\t')
        # Ion
        flg = 2
        if (len(isplit[0].strip()) > 0):# & (isplit[0][0] not in ['1','2']):
            ipos = isplit[0].find('1')
            ionc = isplit[0][0:ipos-1].strip()
            try:
                Zion = xai.name_ion(ionc)
            except KeyError:
                xdb.set_trace()
            flg = 1
        # Column
        csplit = isplit[3].split(' ')
        clm = float(csplit[0])
        sig = float(csplit[2])
        if flg == 1:
            ion_dict[ionc] = dict(clm=clm, sig_clm=sig, flg_clm=1, Z=Zion[0],ion=Zion[1])
        else: # Add it in
            tmp_dict = dict(clm=clm, sig_clm=sig, flg_clm=1, Z=Zion[0],ion=Zion[1])
            logN, siglogN = xiai.sum_logN(ion_dict[ionc], tmp_dict)
            ion_dict[ionc]['clm'] = logN
            ion_dict[ionc]['sig_clm'] = siglogN
    ions = ion_dict.keys()

    # Now Table 2 for the extras
    with open(tab_fils[1],'r') as f:
        flines2 = f.readlines()
    # Trim the first 10 lines
    flines2 = flines2[10:]
    # Loop
    for iline in flines2:
        isplit = iline.split('\t')
        #
        ionc = isplit[0].strip()
        if (len(ionc) == 0) or (ionc in ions):
            continue
        #
        Zion = xai.name_ion(ionc)
        ion_dict[ionc] = dict(Z=Zion[0], ion=Zion[1], sig_clm=0.)
        if isplit[4][0] == '<':
            ion_dict[ionc]['clm'] = float(isplit[4][1:])
            ion_dict[ionc]['flg_clm'] = 3
        else:
            raise ValueError('Should not get here')


    # Finish
    lls._ionclms = IonClms(idict=ion_dict)
    lls.Refs.append('Tri05')
    return lls

def peroux06a():
    '''Peroux, C. et al. 2006a, MNRAS, 372, 369
    SDSS J0134+0051
    One of her sample
    Metal columns taken by JXP from Table 2 (no online data)
    Total NHI from damping wings
    ''' 
    # Setup
    radec = xor.stod1('J013405.75+005109.4') # SDSS Name
    lls = LLSSystem(name='SDSSJ0134+0051_z0.842', RA=radec[0], Dec=radec[1], zem=1.522,
        zabs=0.842, vlim=[-150., 150.]*u.km/u.s, NHI=19.93, sigNHI=np.array([0.15,0.15]))
    #  Table 2
    ion_dict = {}
    N = np.sum(np.array([5.56,12.6,13.7,23.5,61.4,39.8,6,9.14])*1e10)
    sig = np.sqrt(np.sum((np.array([2.32,3.1,3.68,4.13,8.02,6.65,3.37,2.82])*1e10)**2))
    ion_dict['Mg I'] = dict(clm=np.log10(N), sig_clm=sig/N/np.log(10),flg_clm=1,Z=12,ion=1)
    ion_dict['Mg II'] = dict(clm=np.log10(5e13), sig_clm=0.,flg_clm=2,Z=12,ion=2)
    N = np.sum(np.array([8.17,4.28,32.1,125,710,301,893,600,263,65.7])*1e11)
    sig = np.sqrt(np.sum((np.array([2.63,1.40,2.37,8.6,53.2,28.4,73.5,61.7,14.0,2.95])*1e11)**2))
    ion_dict['Fe II'] = dict(clm=np.log10(N), sig_clm=sig/N/np.log(10),flg_clm=1,Z=26,ion=2)
    sig = np.sqrt(np.sum((np.array([3.72,1.84,2.36,3.83])*1e11)**2))
    ion_dict['Zn II'] = dict(clm=np.log10(2*sig), sig_clm=0.,flg_clm=3,Z=30,ion=2)
    sig = np.sqrt(np.sum((np.array([19.4,9.79])*1e11)**2))
    ion_dict['Cr II'] = dict(clm=np.log10(2*sig), sig_clm=0.,flg_clm=3,Z=24,ion=2)
    # Not including MnII.  Appears as a detection but also given as a limit..

    # Finish
    lls._ionclms = IonClms(idict=ion_dict)
    lls.Refs.append('Prx06a')
    return lls
 
def peroux06b():
    '''Peroux, C. et al. 2006b, A&A, 450, 53
    SDSS J1323-0021
    Metal rich
    Metal columns copied by JXP from Table 1 
    Total NHI from damping wings
    ''' 
    # Setup
    radec = xor.stod1('J132323.78-002155.2') # SDSS Name
    lls = LLSSystem(name='SDSSJ1323-0021_z0.716', RA=radec[0], Dec=radec[1], zem=1.390,
        zabs=0.716, vlim=[-200., 200.]*u.km/u.s, NHI=20.21, sigNHI=np.array([0.20,0.20]))
    # Parse table file
    tab_fil = xa_path+"/data/LLS/peroux06b.tb1.ascii"
    with open(tab_fil,'r') as f:
        flines = f.readlines()
    ion_dict = {}
    for iline in flines:
        isplit = iline.split('\t')
        if len(isplit[0]) == 0:
            # Grab ions and init
            ions = isplit[3:10]
            for ion in ions:
                Zion = xai.name_ion(ion)
                ion_dict[ion] = dict(clm=0., sig_clm=0.,flg_clm=1,Z=Zion[0],ion=Zion[1])
            continue
        # Column or sigma?
        if isplit[0][0] == 'N': # Column
            for kk,iis in enumerate(isplit[3:10]):
                ion = ions[kk]
                if iis[0] == '>':
                    ion_dict[ion]['flg_clm'] == 2
                    ion_dict[ion]['clm'] += float(iis[1:])
                elif iis[0] == '<':
                    pass
                elif iis[0] == '.':
                    pass
                else:
                    ion_dict[ion]['clm'] += float(iis)
        else: # Sigma
            for kk,iis in enumerate(isplit[3:10]):
                ion = ions[kk]
                if iis[0] == '.':
                    pass
                else:
                    ion_dict[ion]['sig_clm'] += float(iis)**2
    # Convert to log
    for ion in ions:
        N = ion_dict[ion]['clm']
        sig = np.sqrt(ion_dict[ion]['sig_clm'])
        #
        ion_dict[ion]['clm'] = np.log10(N)
        if ion_dict[ion]['flg_clm'] == 2:
            ion_dict[ion]['sig_clm'] = 0.
        else:
            ion_dict[ion]['sig_clm'] = sig/N/np.log(10)
    # Finish
    lls._ionclms = IonClms(idict=ion_dict)
    lls.Refs.append('Prx06b')
    return lls

def meiring06():
    '''Meiring et al. 2006, MNRAS, 370, 43
    Q1107+0003 
    Taken from Table 4 by JXP
    NHI from RTN06 (damping wings)
    RA/DEC from STIS header
    ''' 
    # Setup
    lls = LLSSystem(name='SDSSJ1107+0003_z0.954', RA=166.90273*u.deg, 
        Dec=0.05795000*u.deg, zem=1.726,
        zabs=0.9542, vlim=[-300., 300.]*u.km/u.s, NHI=20.26, sigNHI=np.array([0.14,0.09]))
    #  Meiring06, Table 4
    ion_dict = {}
    ion_dict['Zn II'] = dict(clm=12.08, sig_clm=0.,flg_clm=3,Z=30,ion=2)
    ion_dict['Ti II'] = dict(clm=13.01, sig_clm=0.,flg_clm=3,Z=22,ion=2)
    ion_dict['Cr II'] = dict(clm=12.76, sig_clm=0.,flg_clm=3,Z=24,ion=2)
    # Finish
    lls._ionclms = IonClms(idict=ion_dict)
    lls.Refs.append('Mei06')
    return lls

def meiring07():
    '''Meiring et al. 2007, MNRAS, 376, 557
    SLLS with Magellan
    Abundances from Table 11 from astro-ph (LateX) by JXP [AODM]
    RA/DEC from Table 1
    ''' 
    all_lls = []
    # Table 1
    tab_fil = xa_path+"/data/LLS/meiring07.tb1.ascii"
    with open(tab_fil,'r') as f:
        flines1 = f.readlines()
    # Grab RA/DEC
    qso_dict = {}
    for iline in flines1:
        if iline[0:2] in ['QS','\h','$\\', 'J2']:
            continue
        # Parse
        isplit = iline.split('&')
        #xdb.set_trace()
        radec = xor.stod1((isplit[2],isplit[3]))
        # zem
        if isplit[0].strip() != 'Q0826-2230':
            zem = float(isplit[5].strip())
        else:
            zem = 0.911
        # Save
        qso_dict[isplit[0].strip()] = dict(RA=radec[0],Dec=radec[1],zem=zem)
    # Abundances (AODM)
    # Table 11
    tab_fil = xa_path+"/data/LLS/meiring07.tb11.ascii"
    with open(tab_fil,'r') as f:
        flines11 = f.readlines()
    #
    ion_dict = {}
    for iline in flines11:
        if iline[0:2] in ['\h','  ']:
            continue
        # Parse
        isplit = iline.split('&')
        # Ions
        if iline[0:2] == 'QS':
            ioncs = []
            Zions = []
            for iis in isplit[3:-1]: # Skipping HI
                # Parse
                is2 = iis.split('\\')
                ip2 = is2[2].find('}')
                ionc = is2[1][2:].strip()+' '+is2[2][0:ip2].strip()
                # Zion
                Zion = xai.name_ion(ionc)
                # Append
                ioncs.append(ionc)
                Zions.append(Zion)
            continue
        if iline[0] == 'Q':
            # QSO
            qso = isplit[0].strip()
            # zabs and name
            zabs = float(isplit[1].strip())
            qso_dict[qso]['name']=qso+'z_{:.3f}'.format(zabs) 
            qso_dict[qso]['zabs']=zabs
            # NHI
            is2 = isplit[2].strip()
            qso_dict[qso]['NHI'] = float(is2[0:5])
            #if qso_dict[qso]['NHI'] >= 20.3:
            #    print('Uh oh.  DLA')
            qso_dict[qso]['sigNHI'] = np.array([float(is2[10:])]*2)
            # Generate LLS
            lls = LLSSystem(**qso_dict[qso])
            continue
        else:
            # ADOM Columns
            ion_dict = {}
            for kk,iis in enumerate(isplit[3:-1]):
                is2 = iis.strip()
                if is2[0:3] == '$>$':
                    ion_dict[ioncs[kk]] = dict(sig_clm=0.,flg_clm=2,Z=Zions[kk][0],ion=Zions[kk][1])
                    ion_dict[ioncs[kk]]['clm'] = float(is2[3:])
                elif is2[0:3] == '$<$':
                    ion_dict[ioncs[kk]] = dict(sig_clm=0.,flg_clm=3,Z=Zions[kk][0],ion=Zions[kk][1])
                    ion_dict[ioncs[kk]]['clm'] = float(is2[3:])
                elif len(is2) == 0:
                    pass
                else:
                    ion_dict[ioncs[kk]] = dict(flg_clm=1,Z=Zions[kk][0],ion=Zions[kk][1])
                    ion_dict[ioncs[kk]]['clm'] = float(is2[0:5])
                    ion_dict[ioncs[kk]]['sig_clm'] = float(is2[10:])
            # Finish
            lls._ionclms = IonClms(idict=ion_dict)
            lls.Refs.append('Mei07')
            all_lls.append(lls)

    # Return SLLS only
    fin_slls = [ills for ills in all_lls if ills.NHI < 20.3]
    return fin_slls


def nestor08():
    '''Nestor, D. et al. 2008, MNRAS, 390, 1670-1682
    Q2149+212
    Taken from Table 1 by JXP
    NHI from RTN06 (damping wings)
    RA/DEC from STIS header
    ''' 
    # Setup
    lls = LLSSystem(name='SDSSJ2151+2130_z1.002', RA=327.94096*u.deg, 
        Dec=21.503750*u.deg, zem=1.534,
        zabs=1.0023, vlim=[-300., 300.]*u.km/u.s, NHI=19.30, sigNHI=np.array([0.10,0.10]))
    #  Meiring06, Table 4
    ion_dict = {}
    ion_dict['Zn II'] = dict(clm=12.13, sig_clm=0.,flg_clm=3,Z=30,ion=2)
    ion_dict['Cr II'] = dict(clm=12.59, sig_clm=0.,flg_clm=3,Z=24,ion=2)
    # Finish
    lls._ionclms = IonClms(idict=ion_dict)
    lls.Refs.append('Nes08')
    return lls
 

#####
def log_sum(logN):
    '''Sum up logN values return the log
    '''
    Nsum = np.sum(10.**np.array(logN))
    return np.log10(Nsum)

######
if __name__ == '__main__':
     
    flg_test = 0
    flg_test += 2**0  # Zonak2004, Jenkins2005

    # Test ions
    if (flg_test % 2**1) >= 2**0:
        #lls = nestor08()
        lls = meiring07()
        #lls = meiring06()
        #lls = peroux06b()
        #lls = peroux06a()
        #lls = tripp2005()
        #lls = jenkins2005()
        #lls = zonak2004()
        print(lls)
        #xdb.set_trace()
    
    # Plot the LLS
