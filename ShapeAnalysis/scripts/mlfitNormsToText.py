#!/usr/bin/env python

import re
from sys import argv, stdout, stderr, exit
from optparse import OptionParser

# import ROOT with a fix to get batch mode (http://root.cern.ch/phpBB3/viewtopic.php?t=3198)
import ROOT
ROOT.gROOT.SetBatch(True)

parser = OptionParser(usage="usage: %prog [options] in.root  \nrun with --help to get list of options")
parser.add_option("-u", "--uncertainties", default=False, action="store_true", help="Report the uncertainties from the fit(s) too")

(options, args) = parser.parse_args()
if len(args) == 0:
    parser.print_usage()
    exit(1)

errors = False
if options.uncertainties: 
    errors = True

file = ROOT.TFile.Open(args[0]);
prefit = file.Get("norm_prefit")
fit_s = file.Get("norm_fit_s")
fit_b = file.Get("norm_fit_b")
if prefit == None: stderr.write("Missing fit_s in %s. Did you run FitDiagnostics in a recent-enough version of combine and with --saveNorm?\n" % file);
if fit_s  == None: raise RuntimeError, "Missing fit_s in %s. Did you run FitDiagnostics with --saveNorm?" % file;
if fit_b  == None: raise RuntimeError, "Missing fit_b in %s. Did you run FitDiagnostics with --saveNorm?" % file;

iter = fit_s.createIterator()
#Headline = "%-30s %-30s     pre-fit   signal+background Fit  bkg-only Fit"%("Channel","Process") if (prefit and errors) else "%-30s %-30s  signal+background Fit  bkg-only Fit"%("Channel","Process")
if prefit and errors :
 headrow  = ["Channel","Process","Pre-fit","S+B Fit","B-Only Fit"]
 headline = ("{:40} {:25} {:^25} {:^25} {:^25}").format(*headrow)
elif prefit: 
 headrow  = ["Channel","Process","Pre-fit","S+B Fit","B-Only Fit"]
 headline = ("{:40} {:25} {:>20} {:>20} {:>20}").format(*headrow)
else : 
 headrow = ["Channel","Process","S+B Fit","B-Only Fit"]
 headline = ("{:40} {:25} {:>20} {:>20}").format(*headrow)

line = "".join(["-" for i in range(len(headline))])
print headline
print line

while True:
    norm_s = iter.Next()
    if norm_s == None: break;
    norm_b = fit_b.find(norm_s.GetName())
    norm_p = prefit.find(norm_s.GetName()) if prefit else None
    # we have to replace any non-standard characters with "_" otherwise the matching will screw up 
    proc_chan_name = (norm_s.GetName()).replace(".","_").replace(":","_").replace(",","_")
    m = re.match(r"(\w+)/(\w+)", proc_chan_name);
    if m == None: m = re.match(r"n_exp_(?:final_)?(?:bin)+(\.\w+)_proc_(\.\w+)", proc_chan_name);
    if m == None: raise RuntimeError, "Non-conforming object name %s" % norm_s.GetName()
    if norm_b == None: raise RuntimeError, "Missing normalization %s for background fit" % norm_s.GetName()
    if prefit and norm_p and errors:
        row = ["%-40s"%m.group(1), "%-25s"%m.group(2), "%10.3f +/- %-10.3f"%(norm_p.getVal(), norm_p.getError()), "%10.3f +/- %-10.3f"%(norm_s.getVal(), norm_s.getError()),"%10.3f +/- %-10.3f"%(norm_b.getVal(), norm_b.getError())]
	print("{:<40} {:25} {:10} {:10} {:10}").format(*row)
        #print "%-30s %-30s % 7.3f +/- % 7.3f % 7.3f +/- % 7.3f  % 7.3f +/- % 7.3f" % 
    else:
        if norm_p and prefit:
            row = ["%-40s"%m.group(1), "%-25s"%m.group(2), "%10.3f"%(norm_p.getVal()), "%10.3f"%(norm_s.getVal()),"%10.3f"%(norm_b.getVal())]
	    print("{:<40} {:25} {:>20} {:>20} {:>20}").format(*row)
            #print "%-30s %-30s %7.3f %7.3f %7.3f" % (m.group(1), m.group(2), norm_p.getVal(),  norm_s.getVal(),  norm_b.getVal())
        else:
            row = ["%-40s"%m.group(1), "%-25s"%m.group(2), "%10.3f"%(norm_s.getVal()),"%10.3f"%(norm_b.getVal())]
	    print("{:<40} {:25} {:>20} {:>20}").format(*row)
            #print "%-30s %-30s %7.3f %7.3f" % (m.group(1), m.group(2), norm_s.getVal(), norm_b.getVal())

# Get totals and data as well?
categories = [key.GetName() for key in file.Get('shapes_prefit').GetListOfKeys()]
for cat in categories:
    for total in ['total','total_signal','total_background']:
        vals = []
        for fit in ['prefit','fit_s','fit_b']:
            hist = file.Get("shapes_"+fit+"/"+cat+"/"+total)
            err = ROOT.Double()
            norm = hist.IntegralAndError(1,hist.GetNbinsX(),err)
            vals += [norm,err]

        if prefit and norm_p and errors:
            row = ["%-40s"%cat, "%-25s"%total, "%10.3f +/- %-10.3f"%(vals[0],vals[1]), "%10.3f +/- %-10.3f"%(vals[2],vals[3]),"%10.3f +/- %-10.3f"%(vals[4],vals[5])]
            print("{:<40} {:25} {:10} {:10} {:10}").format(*row)
        else:
            if norm_p and prefit:
                row = ["%-40s"%cat, "%-25s"%total, "%10.3f"%(vals[0]), "%10.3f"%(vals[2]),"%10.3f"%(vals[4])]
                print("{:<40} {:25} {:>20} {:>20} {:>20}").format(*row)
            else:
                row = ["%-40s"%cat, "%-25s"%total, "%10.3f"%(vals[2]),"%10.3f"%(vals[4])]
                print("{:<40} {:25} {:>20} {:>20}").format(*row)

    tgr = file.Get('shapes_prefit/'+cat+'/data')
    data = sum(list(tgr.GetY()))

    if prefit and norm_p and errors:
        row = ["%-40s"%cat, "%-25s"%('Data'), "%10.3f +/- %-10.3f"%(data,0), "%10.3f +/- %-10.3f"%(data,0),"%10.3f +/- %-10.3f"%(data,0)]
        print("{:<40} {:25} {:10} {:10} {:10}").format(*row)
    else:
        if norm_p and prefit:
            row = ["%-40s"%cat, "%-25s"%('Data'), "%10.3f"%(data), "%10.3f"%(data),"%10.3f"%(data)]
            print("{:<40} {:25} {:>20} {:>20} {:>20}").format(*row)
        else:
            row = ["%-40s"%cat, "%-25s"%('Data'), "%10.3f"%(data),"%10.3f"%(data)]
            print("{:<40} {:25} {:>20} {:>20}").format(*row)



