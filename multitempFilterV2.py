# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 18:24:11 2022

@author: Frank De Grandi 2022
"""

from localmeanV2 import localmeanV2
import numpy as np
from wavsoftdenoise import writehdr
from wavtrans import wavtransform
from noiseEst import homoarea

# dir: imput data sets directory
# filelist: array of input data sets file names
# data sets are co-registered equal geometry float32 detected  (ENVI 4 data type)
# wavdir: directory for wavelet data representation
# outfileroot: root filename of filetered data sets
# dp: number of pixel in the input datat set
# dl: number of lines in the input data set
# skipdwt: switch set to 1 to skip the wavelet transform step
# skiplmean: set to one to skip noise estimation step

def multitempfilterV2(dir, filelist, wavdir, outfileroot, dp, dl, skipdwt, skiplmean):
    nf = len(filelist)
    for j in range(nf):
        wavtransform(dir, filelist[j], wavdir, outfileroot+str(j+1), dp, dl, skipdwt)
    blockpos=homoarea(wavdir, filelist[0]+'_log', dp, dl)
    xmin=blockpos[0]
    ymin=blockpos[1]
    if (skiplmean == 0):
        for j in range(nf):
            print('processing file: ', filelist[j])
            outfile = outfileroot+str(j+1)
            localmeanV2(dir, filelist[j], wavdir, outfile, xmin, ymin, dp, dl)
    dir = dir+'/'
    
    # wighted average of the data 
    filesd=[dir+filelist[0]]
    for i in range(nf-1):
        filesd=filesd+([dir+filelist[i+1]])
    print(filesd)
    
    filesreco = [wavdir+'/'+outfileroot+str(1)+'_reco']
    filesout=[dir+outfileroot+str(1)+'_filt']
    for i in range(nf-1):
        filesreco = filesreco+([wavdir+'/'+outfileroot+str(i+2)+'_reco'])
        filesout=filesout+[dir+outfileroot+str(i+2)+'_filt']
    print(nf)
    print(filesout)
    print(filesreco)
    
    bs=512
    nb = int(dl/bs)
    rem = dl % bs
    inwin=np.ones([bs, dp, nf], dtype='float32')
    inwinrem = np.ones([rem, dp, nf], dtype='float32')
    inwinrec=np.ones([bs, dp, nf], dtype='float32')
    inwinrecrem=np.ones([rem, dp, nf], dtype='float32')
    weights = np.ones([bs, dp, nf, nf], dtype='float32')
    weightsrem=np.ones([rem, dp, nf, nf], dtype='float32')
    outwin=np.zeros([bs, dp], dtype='float32')
    outwinrem=np.zeros([rem, dp], dtype='float32')
    
    
        
    bckf = [open(i, 'rb') for i in filesd]   
    meanvf = [open(i, 'rb') for i in filesreco]
    outf=[open(i, 'wb') for i in filesout]
    # read one block of all input files
    for j in range(nb):
        k=0
        #for f in bckf:
        for k in range(nf):
            buf=np.fromfile(bckf[k], dtype='float32', count=dp*bs)
            bufs = buf.reshape(bs, dp)
            inwin[0:bs, 0:dp, k]=bufs
        
        k=0
        for fr in meanvf:
            bufrec=np.fromfile(fr, dtype='float32', count=dp*bs)
            bufresh = bufrec.reshape(bs, dp)
            inwinrec[0:bs, 0:dp, k]=bufresh
            k = k+1
            # prepare wrights for average
        for p1 in range(nf):
            for p2 in range(nf):
                weights[0:bs, 0:dp, p1, p2] = inwinrec[0:bs, 0:dp, p1] / inwinrec[0:bs, 0:dp, p2]
        print('weights: ', weights.shape)
        for p1 in range(nf):
            print('Filtering set', p1)
            # average
            outwin[0:bs, 0:dp] = 0.0
            for p2 in range(nf):
                outwin=outwin+inwin[0:bs, 0:dp, p2] * weights[0:bs, 0:dp, p1, p2]
            outf[p1].write(outwin / float(nf))
            
            # process last block if remainder is not 0
    if (rem != 0):
        k=0
        for f in bckf:
             buf=np.fromfile(f, dtype='float32', count=dp*rem)
             bufs = buf.reshape(rem, dp)
             inwinrem[0:rem, 0:dp, k]=bufs
             k = k+1
            
        k=0
        for fr in meanvf:
            bufrec=np.fromfile(fr, dtype='float32', count=dp*rem)
            bufresh = bufrec.reshape(rem, dp)
            inwinrecrem[0:rem, 0:dp, k]=bufresh
            k = k+1
            # prepare wrights for average
        for p1 in range(nf):
            for p2 in range(nf):
                weightsrem[0:rem, 0:dp, p1, p2] = inwinrecrem[0:rem, 0:dp, p1] / inwinrecrem[0:rem, 0:dp, p2]
        for p1 in range(nf):
            outwinrem[0:rem, 0:dp] = 0.0
            for p2 in range(nf):
                outwinrem = outwinrem+inwinrem[0:rem, 0:dp, p2] * weightsrem[0:rem, 0:dp, p1, p2]
            print('weights: ', weightsrem.shape)
            
            outf[p1].write(outwinrem / float(nf))
        
        
    for i in range(nf):
        writehdr(dir, outfileroot+str(i+1)+'_filt', dp, dl)
    for f in outf:
        f.close
    for f in bckf:
        f.close()
    for f in meanvf:
        f.close
        
    
       
      