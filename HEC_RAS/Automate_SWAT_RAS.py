import datetime
import urllib
#import urllib2
import subprocess
# import requests
#import h5py
# import pandas as pd
import os
import shutil
#import numpy as np
# import rasterio
#import csv
import glob
import paramiko
from scp import SCPClient

homedir=r"D:/SASWMS_Shahryar/houston/SWATprep"
class HoustonSimulation():
    def __init__(self,nd):
        self.todaydate = datetime.date.today()
        self.noforedays = 3
        self.swatstartdate = datetime.datetime.combine(datetime.date(2017,1,1), datetime.time(0,0))
        self.forestartdate =  datetime.datetime.combine(self.todaydate, datetime.time(0,0)) + datetime.timedelta(days=nd)  #-2
        
        self.foreenddate = self.forestartdate + datetime.timedelta(days=self.noforedays)
#        self.foreenddate = datetime.datetime.combine(self.todaydate, datetime.time(0,0)) + datetime.timedelta(days=self.noforedays)
        
#        self.imergprcpdate = datetime.datetime.combine(self.todaydate, datetime.time(0,0)) + datetime.timedelta(days=-1)
        self.rasstartdate = self.forestartdate + datetime.timedelta(days=-8)
        # self.visstartdate = self.forestartdate + datetime.timedelta(days=-21)
        
        # self.conn = sqlite3.connect('Insituwaterlevel.db')
        print self.todaydate, self.forestartdate, self.foreenddate

    def download_Precip(self,ftype):
        text = urllib.URLopener()
        enddate = self.forestartdate 
        preciptime = (enddate + datetime.timedelta(days=-1)).strftime('%Y%m%d') 
        wrftime=enddate.strftime('%Y%m%d')
        # IMERG
        print "Downloading IMERG:",  preciptime + ".houston.precip.txt" 
        try:
            text.retrieve("http://128.95.29.64/datasets/IMERG/" + preciptime + ".houston.precip.txt" , "D:/SASWMS_Shahryar/houston/SWATprep/Precipitation/IMERG/" + preciptime + ".houston.precip.txt" )
        except:
            print "IMERG not available"

                
        # WRF, or GFS if WRF unavailable
        for lead in range(self.noforedays+1):
            print "Downloading WRF:",  wrftime + ".houston.precip.gfs.L" + str(lead) + ".txt" 
            try: 
                text.retrieve("http://128.95.29.64/datasets/WRF_Downscaled/" + wrftime + "/" + wrftime + ".houston.precip.gfs.L" + str(lead) + ".txt" , "D:/SASWMS_Shahryar/houston/SWATprep/Precipitation/" + ftype + "/" + wrftime + ".houston.precip.gfs.L" + str(lead) + ".txt" )
            except:
                print "WRF not available, downloading GFS:",  wrftime + ".houston.precip.gfs.L" + str(lead) + ".txt" 
                try: 
                    text.retrieve("http://128.95.29.64/datasets/GFSForecast/" + wrftime + "/" + wrftime + ".houston.precip.gfs.L" + str(lead) + ".txt" , "D:/SASWMS_Shahryar/houston/SWATprep/Precipitation/" + ftype + "/" + wrftime + ".houston.precip.gfs.L" + str(lead) + ".txt" )
                except:
                    print "GFS precip not available"
            

                
    def swatforcing(self, hindcast="IMERG"):
        enddate = self.forestartdate 
        print 'swatforcing'        
        ncols =   12
        nrows =   13
        xllcorner = -96.0
        yllcorner =  29.5
        cellsize  =  0.1

        preciptime = (enddate + datetime.timedelta(days=-1)).strftime('%Y%m%d') #20180103.precip.houston.txt
        precippath = homedir+'/Precipitation/IMERG/' + preciptime + '.houston.precip.txt'
        print 'Writing from: '+ preciptime + '.houston.precip.txt'
        strcontent = open(precippath, 'r')
        lines = strcontent.readlines()
        
        for i in xrange(nrows):
            lat = yllcorner+cellsize*(nrows-0.5-i)
            elements = lines[i+6].split(' ')
            
            for j in range(ncols):
                lon=xllcorner+cellsize*(j+0.5)
                forcingfile = homedir+'/SWATInput/IMERG/p' + "{0:.2f}".format(lat) + '_' + "{0:.2f}".format(lon) + '.txt'
                forcingline = "{0:.2f}".format(float(elements[j+1]))
                header = "20170101\n"
                if not os.path.exists(forcingfile):
                    with open(forcingfile, 'w') as txt:
                    	txt.write(header)
                with open(forcingfile, 'a') as txt:
                    txt.write(forcingline + '\n')
#
        for ftype in ['GFS']:
            if os.path.exists( homedir+'/SWATInput/' + ftype + r'/' + enddate.strftime("%Y%m%d")) == False:
                os.makedirs( homedir+'/SWATInput/' + ftype + r'/' + enddate.strftime("%Y%m%d"))

            for i in xrange(nrows):
                    lat = yllcorner+cellsize*(nrows-0.5-i)
                    for j in range(ncols):
                        lon=xllcorner+cellsize*(j+0.5)
                        forcingfile = homedir+'/SWATInput/IMERG/p' + "{0:.2f}".format(lat) + '_' + "{0:.2f}".format(lon) + '.txt'
                        outfile = homedir+'/SWATInput/' + ftype + r'/' + enddate.strftime("%Y%m%d") + '/p' + "{0:.2f}".format(lat) + '_' + "{0:.2f}".format(lon) + '.txt'
                        shutil.copy(forcingfile, outfile)
#    
          
            for frst in range(self.noforedays+1):
                frsttime = datetime.timedelta(days=frst)
                print (enddate + frsttime).strftime("%Y%m%d")
                frstpath = homedir+'/Precipitation/' + ftype + r'/' + enddate.strftime("%Y%m%d") + '.houston.precip.gfs.L' + str(frst) + '.txt' #20190901.houston.precip.gfs.L3
                strcontent = open(frstpath, 'r')
                lines = strcontent.readlines()
                for i in range(nrows):
                    elements = lines[i+6].split(' ')   
                    lat = yllcorner+cellsize*(nrows-0.5-i)
                    for j in range(ncols):
                        lon=xllcorner+cellsize*(j+0.5)
                        forcingfile = homedir+'/SWATInput/' + ftype + r'/' + enddate.strftime("%Y%m%d") + '/p' + "{0:.2f}".format(lat) + '_' + "{0:.2f}".format(lon) + '.txt'
                        forcingline = "{0:.2f}".format(float(elements[j+1]))
                        with open(forcingfile, 'a') as txt:
                            txt.write(forcingline + '\n')
#    
        print 'Done forcing'
    
    def swatprecipprep(self, ftype='GFS'):
        print 'swatprecipprep'        
        templatepath=homedir+r"/pcpHoustonSample1.pcp"
        precippath = homedir+"/SWATModel_" + ftype[0:3] + "/pcp1.pcp"
        startdate = self.swatstartdate
        forecastdate = self.forestartdate
        enddate = self.foreenddate
        ffile = open(templatepath, 'r')
        lines = ffile.readlines()
        stations=lines[0].replace('Station  ','').replace(',\n','').split(',')
        days = (enddate - startdate).days + 1
        print(days)
        pcp=[]
        for i in xrange(days):
            x=datetime.timedelta(days=i)
            pcp.append(datetime.datetime.strftime(startdate+x, "%Y%j"))
            
#        print pcp
        print pcp[len(pcp)-1]
        print len(pcp)
        print stations
        for station in stations:
            p = open(homedir+'/SWATInput/' + ftype + r'/' + forecastdate.strftime("%Y%m%d") + '/' + station + '.txt', 'r')
            plines=p.readlines()
            print 'plines', len(plines)
            for j in range(1,len(pcp)+1):
#                print j,plines[j-1]
                pcp[j-1]=pcp[j-1]+ '{0:.1f}'.format(float(plines[j].rstrip())).zfill(5)     #CHECK plines[j-1]
        print pcp[0]
        strcontent = lines[0] + lines[1] + lines[2] + lines[3] + "\n".join(pcp)
    
        with open(precippath,'w') as txt:
            txt.write(strcontent)
        print "Successful precipprep"
     
    def swatsimulation(self, ftype='GFS'):
        configpath=r"D:/SASWMS_Shahryar/houston/SWATprep/SWATModel_GFS/file.cio"
        startdate = self.swatstartdate
        startyear = int(startdate.strftime("%Y"))
        enddate= self.foreenddate
        print 'swatdate',startdate,enddate
        year=int(datetime.datetime.strftime(enddate, "%Y"))
        julianday=datetime.datetime.strftime(enddate, "%j")
    
        simyr=year-startyear+1
        ffile = open(configpath, 'r')
        lines = ffile.readlines()
    
        line7 = list(lines[7])
        line7[15] = str(simyr)
        lines[7] = ''.join(line7)
    
        line10 = list(lines[10])
        if len(julianday)==1:
            line10[13]=' '
            line10[14]=' '
            line10[15]=julianday
        elif len(julianday)==2:
            line10[13]=' '
            line10[14]=julianday[0]
            line10[15]=julianday[1]
        else:
            line10[13]=julianday[0]
            line10[14]=julianday[1]
            line10[15]=julianday[2]
    
        lines[10] = ''.join(line10)
    
        ffile=open(configpath,'w')
        ffile.write("".join(lines))
        print "Running swat.."
        os.chdir("D:/SASWMS_Shahryar/houston/SWATprep/SWATModel_GFS/")
        p = subprocess.Popen("./swat2012.exe")
        p.wait()
        print "Finished swat run"
#        os.chdir("../Bin")
        shutil.copy('output.rch', '../SWATOutput/Results_SWAT_' + ftype + '_' + self.forestartdate.strftime("%Y%m%d") + '.rch')

    def swatoutputprocessor(self, ftype='GFS'):
        os.chdir("D:/SASWMS_Shahryar/houston/SWATprep/SWATModel_GFS/")
        stations = {'u1':7,'u1s': 8,'u2':9,'u2s':10,'u3':14,'dn':20,'u13':13,'u15':15,'u16':16,'u17':17,'u18':18,'u19':19,'u21':21} #,'Lalakhal':38,'Tamabil':30,'Patrokhola':206,'Sharifpur':187,'Fultola':148,'Nakuagaon':47,'Malijhi':26,'Chelakhali':25,'Bijoypur':66,'Nitai':68,'Sunamganj':39,'Jadukata':49,'DoyarBazar':41,'Bichanakandi':34,'Lourergarh':57}
        reach=['u1', 'u1s', 'u2', 'u2s', 'u3', 'dn','u13','u15','u16','u17','u18','u19','u21'] #, 49, 41, 66, 30, 38, 58,76, 110, 119, 148, 187, 206, 217, 34, 196]
        print "num reaches",len(reach)

        
        start = self.forestartdate.strftime("%Y%m%d")
        if os.path.exists(r'../SWATOutput/' + ftype + r'/' + start) == False:
            os.makedirs(r'../SWATOutput/' + ftype + r'/' + start)
        u1a=[]
        u1b=[]
        u2a=[]
        u2b=[]
        u13,u15,u16,u17,u18,u19,u21=[],[],[],[],[],[],[]
        
        u3=[]
        dn=[]
        for reac in xrange(len(reach)):
            fname = '../SWATOutput/' + ftype + r'/' + start  + '/' + str(reach[reac]) + '.txt'
            print "processing reach ",reach[reac]
            with open(fname, 'w') as txt:
                txt.write('')

            infile = '../SWATOutput/Results_SWAT_' + ftype + '_' + start + '.rch'
            filep = open(infile, 'r')
            reader = filep.readlines()
            for i in range(10, len(reader)):
                lines=reader[i].split()
#                print lines
                sreach=stations[reach[reac]]
                if int(lines[1].strip())==sreach:
                    if sreach == 7:
                        u1a.append(float(lines[6]))     
                    if sreach == 8:
                        u1b.append(float(lines[6]))
                    if sreach == 9:
                        u2a.append(float(lines[6]))
                    if sreach == 10:
                        u2b.append(float(lines[6]))
                    if sreach == 14:
                        u3.append(float(lines[6]))
                    if sreach == 20:
                        dn.append(-1.0*float(lines[6]))
                    # more u/s stations
                    if sreach == 13:
                        u13.append( float(lines[6]))
                    if sreach == 15:
                        u15.append( float(lines[6]))
                    if sreach == 16:
                        u16.append( float(lines[6]))
                    if sreach == 17:
                        u17.append( float(lines[6]))
                    if sreach == 18:
                        u18.append( float(lines[6]))
                    if sreach == 19:
                        u19.append( float(lines[6]))
                    if sreach == 21:
                        u21.append( float(lines[6]))
                  
        u1=[x + y for x, y in zip(u1a, u1b)]
        u2=[x + y for x, y in zip(u2a, u2b)]
        for reac in xrange(len(reach)):
            fname = '../SWATOutput/' + ftype + r'/' + start  + '/' + str(reach[reac]) + '.txt'
            with open(fname, 'w') as txt:
                txt.write('')
            with open(fname, 'a') as txt:
                if reach[reac]=='u1' or reach[reac]=='u1s':
                    for item in u1:
                        txt.write("%s\n" % item)
                elif reach[reac]=='u2' or reach[reac]=='u2s':
                    for item in u2:
                        txt.write("%s\n" % item)
                elif reach[reac]== 'u3':   
                    for item in u3:
                        txt.write("%s\n" % item)
                elif reach[reac]== 'dn':   #-ve for most downstream
                    for item in dn:
                        txt.write("%s\n" % item)
                # more u/s stations
                elif reach[reac]== 'u13':   
                    for item in u13:
                        txt.write("%s\n" % item)
                elif reach[reac]== 'u15':   
                    for item in u15:
                        txt.write("%s\n" % item)
                elif reach[reac]== 'u16':   
                    for item in u16:
                        txt.write("%s\n" % item)
                elif reach[reac]== 'u17':   
                    for item in u17:
                        txt.write("%s\n" % item)
                elif reach[reac]== 'u18':   
                    for item in u18:
                        txt.write("%s\n" % item)
                elif reach[reac]== 'u19':   
                    for item in u19:
                        txt.write("%s\n" % item)
                elif reach[reac]== 'u21':   
                    for item in u21:
                        txt.write("%s\n" % item)

                    
        startdate = self.swatstartdate + datetime.timedelta(days=365);
        if os.path.exists(r'../FinalOutputs/Inflow/' + ftype + r'/' + start) == False:
            os.makedirs(r'../FinalOutputs/Inflow/' + ftype + r'/' + start)
            
        for reac in xrange(len(reach)):
            startdate = self.swatstartdate + datetime.timedelta(days=365);
            strcontent = "Date,Streamflow(cfs)\n"
            infile = open('../SWATOutput/' + ftype + r'/' + start  + '/' + str(reach[reac]) + '.txt', 'r')
            outfile = r'../FinalOutputs/Inflow/' + ftype + r'/' + start + r'/' + str(reach[reac]) + '_' + start + '.txt'
            fcontent = infile.readlines()
            for line in fcontent:
                if str(reach[reac])=='dn':
                    startdate = startdate+ datetime.timedelta(days=1)
    #                if startdate>=self.visstartdate:
                    if startdate<self.forestartdate:
                        #Cms to cfs
                        strcontent = strcontent + startdate.strftime("%Y-%m-%d") + ',' + "{0:0.1f}".format(float(line.rstrip())*-1.0*35.315) + ',,' + '\n'
                    elif startdate == self.forestartdate:
                        strcontent = strcontent + startdate.strftime("%Y-%m-%d") + ',' + "{0:0.1f}".format(float(line.rstrip())*-1.0*35.315) + ',' + "{0:0.1f}".format(float(line.rstrip())*-1.0*35.315) + '\n'
                    else:
                        strcontent = strcontent + startdate.strftime("%Y-%m-%d") + ',,' + "{0:0.1f}".format(float(line.rstrip())*-1.0*35.315) + '\n'
                else:
                    startdate = startdate+ datetime.timedelta(days=1)
    #                if startdate>=self.visstartdate:
                    if startdate<self.forestartdate:
                        strcontent = strcontent + startdate.strftime("%Y-%m-%d") + ',' + "{0:0.1f}".format(float(line.rstrip())*35.315) + ',,' + '\n'
                    elif startdate == self.forestartdate:
                        strcontent = strcontent + startdate.strftime("%Y-%m-%d") + ',' + "{0:0.1f}".format(float(line.rstrip())*35.315) + ',' + "{0:0.1f}".format(float(line.rstrip())*35.315) + '\n'
                    else:
                        strcontent = strcontent + startdate.strftime("%Y-%m-%d") + ',,' + "{0:0.1f}".format(float(line.rstrip())*35.315) + '\n'

            with open(outfile, 'w') as txt:
                txt.write(strcontent)
            
    def rasbndgen(self, ftype='GFS'):
        os.chdir("D:/SASWMS_Shahryar/houston/HECRASprep/")
        forecastdate = self.forestartdate.strftime("%Y%m%d")
        todaydate = self.forestartdate
        rsttime = datetime.timedelta(days = -9)
        rstdate = datetime.datetime.strftime(todaydate + rsttime, "%d%b%Y").upper()
        print "Restart date",rstdate

        unsteadyfname = 'HecrasModel100_' + ftype + '/unsteady2Dhouston.u01'
        strcontent = "Flow Title=IMERG_" + ftype + "_Forecast_" + forecastdate + "\nProgram Version=5.07\nUse Restart=-1\nRestart Filename=unsteady2Dhouston.p01." + rstdate + r" 2400.rst" + "\n"
        dates = (self.foreenddate-self.swatstartdate).days + 1
        print dates
        ## 2D flow area precipitation data
        precipGridf = open('PrecipGrids.txt', 'r')
        precipgrids = precipGridf.readlines()
        gridprcp = [0] * dates
        count = len(precipgrids)
        for grid in precipgrids:
            #print grid 
            prcpfile= open(r'../SWATprep/SWATInput/' + ftype + r'/' + forecastdate + '/' + grid.rstrip() + '.txt', 'r')
            #"D:\SWATInputs\20160301\p24.150_90.950.txt"
            prcpdata = prcpfile.readlines()
            for k in range(1, len(gridprcp)+1):
                gridprcp[k-1] = gridprcp[k-1] + float(prcpdata[k])   
        for j in xrange(len(gridprcp)):
            gridprcp[j] = gridprcp[j]/count
    
        # Upstream FLow Data
        flowstations = ['u1','u2','u3','dn']#, 25, 47, 68, 66, 57, 39, 49, 41, 34, 30, 38, 58, 76, 110, 119, 148, 187, 206, 217, 196]
        for station in flowstations:
            strcontent = strcontent + 'Boundary Location=                ,                ,        ,        ,                ,FlowArea_lidar        ,                ,' + str(station) + '                              \nInterval=1DAY\n'
            stationfname = open('../SWATprep/SWATOutput/' +ftype + r'/' + forecastdate +'/' + str(station) + '.txt', 'r')
            stationdata = stationfname.readlines()
            strcontent = strcontent + 'Flow Hydrograph= ' + str(len(stationdata))
            for i in xrange(len(stationdata)/10+1):
                strcontent = strcontent + "\n"
                for j in xrange(10):
                    if i*10+j<len(stationdata):
                        flowval = float(stationdata[i*10+j].rstrip())
                        flowdata = "{0:.1f}".format(flowval)
                        flowdata = flowdata.rjust(8)
                        strcontent = strcontent + flowdata
                        
## FOR Multiplier factor to dn
            if station == 'dn':
                print 'stn dn'
                strcontent = strcontent + '\nStage Hydrograph TW Check=0\nFlow Hydrograph QMult= 2\nFlow Hydrograph Slope= 0.05 \nDSS Path=\nUse DSS=False\nUse Fixed Start Time=True\n'
            else:
                print 'stn-else',station
                strcontent = strcontent + '\nStage Hydrograph TW Check=0\nFlow Hydrograph Slope= 0.05 \nDSS Path=\nUse DSS=False\nUse Fixed Start Time=True\n'
            strcontent = strcontent + 'Fixed Start Date/Time=02Jan2018,00:00\nIs Critical Boundary=False\nCritical Boundary Flow=\n'

        # Writing calculated precipitation data
    
        strcontent = strcontent + 'Boundary Location=                ,                ,        ,        ,                ,FlowArea_lidar        ,                ,                                \n'
        strcontent= strcontent + 'Interval=1DAY\n'
        strcontent = strcontent + 'Precipitation Hydrograph= ' + str(len(gridprcp))
    
        for i in xrange(len(gridprcp)/10+1):
            strcontent = strcontent + "\n"
            for j in xrange(10):
                if i*10+j<len(gridprcp):
                    flowdata = "{0:.1f}".format(gridprcp[i*10+j])
                    flowdata = flowdata.rjust(8)
                    strcontent = strcontent + flowdata
        strcontent = strcontent + '\nStage Hydrograph TW Check=0\nFlow Hydrograph Slope= 0.05 \nDSS Path=\nUse DSS=False\nUse Fixed Start Time=True\n'
        strcontent = strcontent + 'Fixed Start Date/Time=02Jan2017,00:00\nIs Critical Boundary=False\nCritical Boundary Flow=\n'
    
        # Writing unsteady boundary data
        with open(unsteadyfname, 'w') as txt:
            txt.write(strcontent)


    def rasplangen(self, ftype='GFS'):
        os.chdir("D:/SASWMS_Shahryar/houston/HECRASprep/")
        forecastdate = self.forestartdate
        startdeltime = datetime.timedelta(days=-10)
        rstdeltime = datetime.timedelta(days=-7)

        rstdate = datetime.datetime.strftime(forecastdate+rstdeltime, '%d%b%Y')
        startdate = datetime.datetime.strftime(forecastdate+startdeltime, '%d%b%Y')
        enddate = datetime.datetime.strftime(self.foreenddate+datetime.timedelta(days=1), '%d%b%Y')
        
        plantemplate = 'unsteady2Dhouston.pSample'
        fcontent = open(plantemplate, 'r')
        lines = fcontent.readlines()
    #     print lines[0].rstrip()
        lines[0] = 'Plan Title=Plan_' + forecastdate.strftime("%Y%m%d") + '\n'
        print lines[0]
    #     print lines[2].rstrip()
        lines[2] = 'Short Identifier=' + forecastdate.strftime("%Y%m%d") + '\n'
    #     print lines[2]
    #     print lines[3].rstrip()
        lines[3] = 'Simulation Date=' + startdate + ',00:00,' + enddate + ',00:00' + '\n'
    #     print lines[3]
    #     print lines[5]
        lines[5] = 'Flow File=u01' + '\n' 
    #     print lines[5]
    
        lines[88] = 'IC Time=,' + rstdate + ',00:00' + '\n' 
    #     print lines[5]
    
        # Writing unsteady boundary data
        planfname = 'HecrasModel100_' + ftype + '/unsteady2Dhouston.p01'
        with open(planfname, 'w') as txt:
            txt.write(''.join(lines))
        
    def rassimulation(self, ftype = 'GFS'):
        modelpath = r'D:/SASWMS_Shahryar/houston/HECRASprep'
        os.chdir("D:/SASWMS_Shahryar/houston/HECRASprep/")
        simstartdate = self.forestartdate
        dates = []
        for i in xrange(12):    #CHECK 45
            dates.append(self.rasstartdate+datetime.timedelta(hours=24*i))
#        print dates
        strcontent = '\t<Layer Name="' + simstartdate.strftime("%Y%m%d") + '" Type="RASResults" Checked="True" Filename=".\unsteady2Dhouston.p01.hdf">\n\t  <Layer Type="RASGeometry" Filename=".\unsteady2Dhouston.p01.hdf" />'
        for findex in xrange(len(dates)):
            reqdate = dates[findex]
            if reqdate>=simstartdate:
                strcontent = strcontent + '\n' + '\t  <Layer Name="depth" Type="RASResultsMap" Filename=".\\' + simstartdate.strftime("%Y%m%d") + r'\Depth (' + reqdate.strftime("%d%b%Y %H").upper() + ' 00 00).vrt">\n\t\t<LabelFeatures Checked="True" rows="1" cols="1" r0c0="FID" Position="5" Color="-16777216" />\n\t\t<MapParameters MapType="depth" LayerName="Depth" OutputMode="Stored Current Terrain" StoredFilename=".\\' + simstartdate.strftime("%Y%m%d") + '\Depth (' + reqdate.strftime("%d%b%Y %H").upper() + ' 00 00).vrt" Terrain="Terrain" ProfileIndex="' + str(findex) + '" ProfileName="' + reqdate.strftime("%d%b%Y %H").upper() + ':00:00" ArrivalDepth="0" />\n\t  </Layer>'
        strcontent = strcontent + '\n' + '      <Layer Name="velocity" Type="RASResultsMap">\n        <MapParameters MapType="velocity" ProfileIndex="2147483647" ProfileName="Max" />\n      </Layer>\n      <Layer Name="elevation" Type="RASResultsMap" Checked="True">\n        <MapParameters MapType="elevation" ProfileIndex="2147483647" ProfileName="Max" />\n      </Layer>\n    </Layer>\n'
        samplefile = open("unsteady2Dhouston.rasmapSample", 'r')
        samplecontent = samplefile.readlines()
        samplecontent[11] = strcontent     ## 11 depends on rasmap sample file
        with open(r'HecrasModel100_' + ftype + r'/unsteady2Dhouston.rasmap', 'w') as txt:
            txt.write(''.join(samplecontent))
            
            
        print "Running hecras for", simstartdate.strftime("%Y%m%d")
        import win32com.client
        hec = win32com.client.Dispatch("RAS507.HECRASController")
#        hec.showRas()
        rasproject = os.path.join(modelpath +  r"/HecrasModel100_" + ftype + "/unsteady2Dhouston.prj")
        hec.Project_Open(rasproject)
        NMsg,TabMsg,block = None,None,True
        hec.Compute_CurrentPlan(NMsg,TabMsg,block)
        hec.QuitRas()
        del hec
        
    def mappreparation(self):
        os.chdir("D:/SASWMS_Shahryar/houston/")

        strdate = self.forestartdate.strftime("%Y%m%d")
        enddate = self.forestartdate 
        preciptime = (enddate + datetime.timedelta(days=-1)).strftime('%Y%m%d') #20180103.precip.houston.txt
        deletetime = (enddate + datetime.timedelta(days=-2)).strftime('%Y%m%d')
        
        if os.path.exists(r'SWATprep/FinalOutputs/GFSPrecipitation/' + strdate) == False:
            os.makedirs(r'SWATprep/FinalOutputs/GFSPrecipitation/' + strdate)
        if os.path.exists(r'SWATprep/FinalOutputs/IMERGPrecipitation/' + preciptime) == False:
            os.makedirs(r'SWATprep/FinalOutputs/IMERGPrecipitation/' + preciptime)
        if os.path.exists(r'SWATprep/FinalOutputs/FloodDepth/GFS/' + strdate) == False:
            os.makedirs(r'SWATprep/FinalOutputs/FloodDepth/GFS/' + strdate)
            
        if os.path.exists(r'HECRASprep/HecrasOutput/WaterSurface/GFS/' + self.forestartdate.strftime("%Y%m%d")) == False:
            os.makedirs(r'HECRASprep/HecrasOutput/WaterSurface/GFS/' + self.forestartdate.strftime("%Y%m%d"))
       
#        # IMERG Preparation     
        os.system('C:\OSGeo4W64\OSGeo4W.bat gdalwarp -overwrite -tr 0.1 0.1 SWATprep/Precipitation/IMERG/' + preciptime + '.houston.precip.txt SWATprep/FinalOutputs/IMERGPrecipitation/Wmm'  + preciptime + '.houston.precip.tif')  
        # mm to in
        os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_calc -A SWATprep/FinalOutputs/IMERGPrecipitation/Wmm'  + preciptime + '.houston.precip.tif --outfile=SWATprep/FinalOutputs/IMERGPrecipitation/W'  + preciptime + '.houston.precip.tif --calc="A/25.4" --NoDataValue=-9999')
            
        os.system('C:\OSGeo4W64\OSGeo4W.bat gdaldem color-relief SWATprep/FinalOutputs/IMERGPrecipitation/W'  + preciptime + '.houston.precip.tif precipitation.txt -alpha SWATprep/FinalOutputs/IMERGPrecipitation/C'  + preciptime + '.houston.precip.tif')
        os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_translate -of PNG SWATprep/FinalOutputs/IMERGPrecipitation/C'  + preciptime + '.houston.precip.tif SWATprep/FinalOutputs/IMERGPrecipitation/' + preciptime + r'/f' + preciptime +'.PNG')
        os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_translate -of AAIGrid  -a_nodata 0 SWATprep/FinalOutputs/IMERGPrecipitation/W'  + preciptime + '.houston.precip.tif SWATprep/FinalOutputs/IMERGPrecipitation/' + preciptime + r'/f' + preciptime +'.asc')
        for filePath in glob.glob('SWATprep/FinalOutputs/IMERGPrecipitation/*'  + preciptime + '*.tif') :
            try:
                os.remove(filePath)
            except:
                print("Error while deleting file : ", filePath)

        # GFSMap Preparation  
        for lead in range(self.noforedays+1):
            os.system('C:\OSGeo4W64\OSGeo4W.bat gdalwarp -overwrite -tr 0.1 0.1 SWATprep/Precipitation/GFS/' + strdate + '.houston.precip.gfs.L' + str(lead) + '.txt SWATprep/FinalOutputs/GFSPrecipitation/W' + strdate + '.m' + str(lead*24).zfill(3) + '.tif')  
            # mm to in
            os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_calc -A SWATprep/FinalOutputs/GFSPrecipitation/W' + strdate + '.m' + str(lead*24).zfill(3) + '.tif --outfile=SWATprep/FinalOutputs/GFSPrecipitation/W' + strdate + '.f' + str(lead*24).zfill(3) + '.tif --calc="A/25.4" --NoDataValue=-9999')
                
            os.system('C:\OSGeo4W64\OSGeo4W.bat gdaldem color-relief SWATprep/FinalOutputs/GFSPrecipitation/W' + strdate + '.f' + str(lead*24).zfill(3) + '.tif precipitation.txt -alpha SWATprep/FinalOutputs/GFSPrecipitation/C' + strdate + '.f' + str(lead*24).zfill(3) + '.tif')
            os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_translate -of PNG SWATprep/FinalOutputs/GFSPrecipitation/C' + strdate + '.f' + str(lead*24).zfill(3) + '.tif SWATprep/FinalOutputs/GFSPrecipitation/' + strdate + r'/f' + str(lead*24).zfill(3) +'.PNG')
            os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_translate -of AAIGrid  -a_nodata 0  SWATprep/FinalOutputs/GFSPrecipitation/W' + strdate + '.f' + str(lead*24).zfill(3) + '.tif SWATprep/FinalOutputs/GFSPrecipitation/' + strdate + r'/f' + str(lead*24).zfill(3) +'.asc')
        for filePath in glob.glob('SWATprep/FinalOutputs/GFSPrecipitation/*'  + strdate + '*.tif') :
            try:
                os.remove(filePath)
            except:
                print("Error while deleting file : ", filePath)
#       
#         #HECRAS Results copy
        for ftype in ['GFS']:
            for fn in os.listdir('HECRASprep/HecrasModel100_'+ ftype +r'/' + strdate + r'/'):
                if '.tif' in fn:
                    print fn[7:25]
                    filedate = datetime.datetime.strptime(fn[7:25], "%d%b%Y %H %M %S")
                    shutil.copy('HECRASprep/HecrasModel100_'+ ftype +r'/' + strdate + r'/' + fn, r'HECRASprep/HecrasOutput/WaterSurface/' + ftype + r'/' + strdate + r'/' + filedate.strftime("%Y%m%d%H") + '.tif')
#         
#            ### delete last day's stored hecras maps
            try:
                shutil.rmtree('HECRASprep/HecrasModel100_'+ ftype +r'/' + deletetime)
            except:
                print("Error while deleting file : ", 'HECRASprep/HecrasModel100_'+ ftype +r'/' + deletetime)
                
            try:
                shutil.rmtree('HECRASprep/HecrasOutput/WaterSurface/' + ftype + r'/' + preciptime)
            except:
                print("Error while deleting file : ", 'HECRASprep/HecrasOutput/WaterSurface/' + ftype + r'/' + preciptime)
#                      
        # HecRAS Flood Map preparation
        for ftype in ['GFS']:
#            for forecasthr in range(6, (self.noforedays+1)*24+1, 6):
            for forecasthr in range(0, (self.noforedays)*24+1, 24):
                reqdate = self.forestartdate + datetime.timedelta(hours = forecasthr)
                print "Processing: ",'HECRASprep/HecrasOutput/WaterSurface/'+ ftype + r'/' + strdate + r'/' + reqdate.strftime("%Y%m%d%H") + '.tif'
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_edit  -a_srs EPSG:5070 ' + 'HECRASprep/HecrasOutput/WaterSurface/'+ ftype + r'/' + strdate + r'/' + reqdate.strftime("%Y%m%d%H") + '.tif') # +  r' SWATprep/FinalOutputs/FloodDepth/'+ 'frp' + str(forecasthr).zfill(3) +'.tif')

                os.system('C:\OSGeo4W64\OSGeo4W.bat gdalwarp -overwrite -tr 10.0 10.0 ' + 'HECRASprep/HecrasOutput/WaterSurface/'+ ftype + r'/' + strdate + r'/' + reqdate.strftime("%Y%m%d%H") + '.tif' +  r' SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'mr' + str(forecasthr).zfill(3) +'.tif')
                # m to ft
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_calc -A SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'mr' + str(forecasthr).zfill(3) +'.tif --outfile=SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'fr' + str(forecasthr).zfill(3) +'.tif --calc="A/0.3048" --NoDataValue=-9999')
                

                
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdalwarp -overwrite -s_srs EPSG:5070  -t_srs EPSG:3857 SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'fr' + str(forecasthr).zfill(3) +'.tif  SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/W' + 'f' + str(forecasthr).zfill(3) +'.tif')
                
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdaldem color-relief   SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/W' + 'f' + str(forecasthr).zfill(3) +'.tif waterlevel_ft.txt -alpha SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/C' + 'f' + str(forecasthr).zfill(3) +'.tif')

                os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_translate -of PNG SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/C' + 'f' + str(forecasthr).zfill(3) +'.tif SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + strdate + r'/f' + str(forecasthr).zfill(3) + '.PNG')
#                
#                # ASCII
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdalwarp  -tr 100.0 100.0 ' + 'HECRASprep/HecrasOutput/WaterSurface/'+ ftype + r'/' + strdate + r'/' + reqdate.strftime("%Y%m%d%H") + '.tif' +  r' SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'mrA' + str(forecasthr).zfill(3) +'.tif')
                # m to ft
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_calc -A SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'mrA' + str(forecasthr).zfill(3) +'.tif --outfile=SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'frA' + str(forecasthr).zfill(3) +'.tif --calc="A/0.3048" --NoDataValue=-9999')  
                
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_translate -of AAIGrid -a_nodata 0 SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'Wf' + str(forecasthr).zfill(3) +'.tif SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + strdate + r'/f' + str(forecasthr).zfill(3) + '.asc')
        
                
                
                # ASCII fr tiff vis
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_edit  -a_srs EPSG:5070 ' + 'HECRASprep/HecrasOutput/WaterSurface/'+ ftype + r'/' + strdate + r'/' + reqdate.strftime("%Y%m%d%H") + '.tif')
                
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdalwarp  -tr 0.1 0.1 ' + 'HECRASprep/HecrasOutput/WaterSurface/'+ ftype + r'/' + strdate + r'/' + reqdate.strftime("%Y%m%d%H") + '.tif' +  r' SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'mrA' + str(forecasthr).zfill(3) +'.tif')
                 # m to ft
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_calc -A SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'mrA' + str(forecasthr).zfill(3) +'.tif --outfile=SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'frA' + str(forecasthr).zfill(3) +'.tif --calc="A/0.3048" --NoDataValue=-9999')  
                
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdalwarp -overwrite -s_srs EPSG:5070  -t_srs EPSG:4326 -te  -96.0229363506 29.4298334866  -94.8252247548  30.8034998041  -tr 0.0005 0.0005 SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'frA' + str(forecasthr).zfill(3) +'.tif  SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/W' + 'f' + str(forecasthr).zfill(3) +'.tif')

                
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_translate -of AAIGrid -a_nodata -9999 SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + 'Wf' + str(forecasthr).zfill(3) +'.tif SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + strdate + r'/f' + str(forecasthr).zfill(3) + '.asc')
    
                os.system('C:\OSGeo4W64\OSGeo4W.bat gdal_translate -of GTiff  SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + strdate + r'/f' + str(forecasthr).zfill(3) + '.asc SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/' + strdate + r'/f' + str(forecasthr).zfill(3) + '.tif')



                
        for filePath in glob.glob('SWATprep/FinalOutputs/FloodDepth/' + ftype + r'/*.tif') :
            try:
                os.remove(filePath)
            except:
                print("Error while deleting file : ", filePath)
#                        

       
        
if __name__ == '__main__':
#    for nd in range(-2,-1):  #(-53,0):
    nd= 0 #0
    forecast = HoustonSimulation(nd)
    for ftype in ['GFS']:
        forecast.download_Precip(ftype)
        forecast.swatforcing('IMERG')
        forecast.swatprecipprep(ftype)     
        forecast.swatsimulation(ftype)
        forecast.swatoutputprocessor(ftype)
        forecast.rasbndgen(ftype)
        forecast.rasplangen(ftype)
        forecast.rassimulation(ftype)
    forecast.mappreparation()
