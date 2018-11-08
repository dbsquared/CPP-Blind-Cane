import json,re,argparse, os
from shutil import copyfile



# Unused, just leave it for future use
def GetLogger (file):
    #headerIncluded = False
    outDict = { "variable":"", "channel":""} 
    for line in file:
        #if '#include "Logger.h"' in line:
        #    headerIncluded = True
        #    continue
        #if headerIncluded & 
        if "Logger" in line:          #static Logger gLogger("channel");
            reOut = re.search('Logger (.*)\(\"(.*)\"\)',line)
            if reOut != None:
                try:
                    outDict["variable"] = reOut.group(1)
                    outDict["channel"] = reOut.group(2)
                    return outDict
                except:
                    continue # do nothing, ignore this line
    return outDict

def BackupFile (fname):
    newFile = fname+".bk"
    if os.path.isfile(newFile):
        return False
    else:
        try:
            copyfile(fname, newFile)
            return True
        except:
            return False
        

def IsLoggerDotHIncluded (file): # Is Logger.h included?
    for line in file:
        if '#include "Logger.h"' in line:
            return True
    return False

def FindFirstRealCode (file): # consider semi-colon the begining of coding
    for idx, line in enumerate(file):
        if ";" in line:
            return idx

def FindOpeningBrackets (file): # add a line of logs after every "{"
    idxList = []
    skipNext = False
    for idx, line in enumerate(file):
        if "class" in line or "typedef" in line: # for class or other type definition, let's skip the outer {
            skipNext = True
        if "{" in line and "}" not in line:  # if "{" and "}" in the same line, can't handle it without making a big change, skip it for now
            if skipNext:
                skipNext = False
                continue 
            else:
                idxList.append(idx)
    return idxList

def InsertBlindCaneLog (file, idx, lineInserted, logLevel):
    file.insert(idx+lineInserted[0]+1, 'blindCaneLogger.'+logLevel+'() << __FILE__ << ":'+ str(idx+1) + ' in " << __FUNCTION__;\n' )
    lineInserted[0] += 1

# TODO: check if blindCaneLoggerLogger is used in source code
# * Avoid variable conflicts
# * Avoid running this program twice for the same source file

def CheckVariableDuplicated (file, prefix):
    for line in file:
        if prefix+"Logger" in line:
            return False
    return True


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Generate')
    parser.add_argument('--files',dest='files', nargs='+', action='store',default=None, help='The source code file(s) you want to add instrumented outputs')
    parser.add_argument('--log-level',dest='logLevel',action='store',default=None,help='The log level for instrumented outputs: debug,info,warn,error')  
    parser.add_argument('--start-line',dest='startLine',action='store',default=1,help='The line number that you want to start adding Blind Cane logs. If not specified, default is the beginning of the file')  
    parser.add_argument('--end-line',dest='endLine',action='store',default=None,help='The line number that you want to stop adding Blind Cane logs. If not specified, default is the end of the file.')  
    

    args=parser.parse_args()
    fileList = args.files
    logLevel = args.logLevel
    startLine = int(args.startLine) -1 # the lineList starts from 0, but human count start from 1
    if args.endLine is not None:
        endLine = int(args.endLine) -1
    else:
        endLine = args.endLine

    if not (logLevel=="debug" or logLevel=="info" or logLevel=="warn" or logLevel=="error"):
        print "Error: Invalid log-level value. Please input one of below:"
        print "debug,info,warn,error"
        exit()
    if startLine < 0:
        print "Error: Invalid start-line, please input number larger than 1"
        exit()
    
    if endLine < 0 and endLine != None:  # none is the implicit default
        print "Error: Invalid end-line, please input number larger than 1"
        exit()
    if endLine < startLine and endLine != None: # none is the implicit default
        print "Error: end-line must greater/equal to start-line"
        exit()

    for file in fileList:
        BackupFile(file)
        lineInserted = [0]   # using list type is stupid, but integer is not mutable data type, but list is https://stackoverflow.com/questions/15148496/passing-an-integer-by-reference-in-python
        fr = open(file, 'r')
        contents = fr.readlines()
        fr.close()
        if endLine is None:
            endLine = len(contents) - 1
        idxList = FindOpeningBrackets(contents)

        if not IsLoggerDotHIncluded(contents):
            contents.insert(0,'#include "Logger.h"\n')
            lineInserted[0] += 1
        contents.insert(FindFirstRealCode(contents)+lineInserted[0]-1, 'static Logger blindCaneLogger("BlindCane"); // Created by C++ Blind Cane\n')
        lineInserted[0] += 1
        
        for idx in idxList:
            if idx <= endLine and idx >= startLine:
                InsertBlindCaneLog(contents,idx,lineInserted, logLevel)   

        contents = "".join(contents)
        fw = open(file, 'w')        
        fw.write(contents)
        fw.close()


        #for line in contents:
        #    print line