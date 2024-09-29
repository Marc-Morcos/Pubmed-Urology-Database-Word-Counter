from concurrent.futures import ThreadPoolExecutor
import re
import csv
import os
import pandas as pd
import numpy as np
import time
from tqdm import tqdm
import json

#get list of words
def getWords(text, filterNums, wordsWeDontWant = []):
    #remove everything but words, digits, whitespace, apostrophe, and dash (replace with space)
    text = re.sub(r'[^\w\d\s\'-]+', ' ', text)

    #lowercase
    text = text.lower()

    #split into words (removes whitespace)
    text=text.split()

    #get rid of 's at END of words
    text = [re.sub("'s$", '', word) for word in text]

    # get rid of numbers
    if(filterNums):
        text = [word for word in text if (not word.isnumeric())]

    # get rid of words we dont want
    text = [word for word in text if (not word in wordsWeDontWant)]

    return text
        

def main():
    stats = dict() #used for other notes

    startTime = time.time()
    print("Starting")

    # word filters
    wordsWeWant = None #"Depression,Anxiety,esteem,Schizophrenia,Borderline personality disorder,stress,personality,emasculation,humiliation,isolation,loneliness,frustration" #None
    wordsWeDontWant = '''thus, p, A, aboard, about, above, abreast, abroad, absent, according, across, adrift, aft, after, afterward, against, ahead, aloft, along, alongside, amid, among, ontop, anti, apropos, around, as, ashore, aslant, astride, at, atop, back, backwards, bar, barring, because, before, beforehand, behind, below, beneath, beside, besides, beyond, but, by, chez, circa, close, come, concerning, contra, contrary, counter, counting, depending, despite, down, downhill, downstairs, downwards, downwind, due, during, east, eastwards, effective, ere, except, excepting, excluding, failing, following, for, forth, forward, from, further, heavenward, hence, henceforth, here, hereby, herein, hereof, hereto, herewith, home, homewards, in, including, indoors, inside, instead, inwards, leftwards, less, like, minus, modulo, near, next, north, northeast, northwest, now, of, offshore, on, onto, onwards, opposite, out, outdoors, outside, outwards, overboard, overhead, overland, overseas, owing, pace, past, pending, per, pertaining, plus, post, pre, prior, pro, qua, re, regarding, regardless, respecting, regards, regard, rightwards, round, sans, seawards, since, skywards, south, southeast, southwards, southwest, sub, thanks, then, thence, thenceforth, there, thereby, therein, thereof, thereto, therewith, throughout, till, times, to, together, touching, towards underfoot, underground, underneath, unlike, until, unto, up, uphill, upon, upstage, upstairs, upwards, upwind, versus, via, vice, wanting, west, westwards, whence, where, whereby, wherein, whereto, wherewith, within, without, worth, although, considering, whilst, while, also, and, additionally, additional, furthermore, as, if, or, to, soon, first, second, third, fourth, however, nonetheless, therefore, similar, similarly, conclusion, the, in, to, and, or, is, patients, cases, are, many, a, between, other, at, per, no, for, it, has, been, such, as, most, become, an, often, will, the, of, was, in, and, it, to, not, into, used, use, had, a, when, as, is, be, by, in, are, can, well, unless, or, who, have, than, for, an, more, on, under, it, with, was, were, Ago, apart, aside, away, notwithstanding, on, over, short, through, I,  you, he, she, it, we, they, my, your, his, her, its, our, their, this, that, these, those, who, whom, which, what, whose, all, any, each, every, none, some, anybody, anyone, anything, myself, yourself, himself, herself, itself, ourselves, themselves,'''
    filterNums = True #if true, filter out words that are entirely numbers

    wordsWeDontWant = set(getWords(wordsWeDontWant,filterNums))
    
    if(wordsWeWant is not None):
        wordsWeWant = set(getWords(wordsWeWant,filterNums))
        for word in wordsWeWant:
            if(word in wordsWeDontWant):
                raise Exception(f"Cant have word in both wordsWeWant and wordsWeDontWant: '{word}'")
        print("Edited wordswewant list to look like the following:",wordsWeWant)
    
    stats["words_filtered_out"] = str(wordsWeDontWant)
    stats["filter_out_numbers"] = str(filterNums)
    stats["words_that_were_specifically_tested"] = str(wordsWeWant)

    #change directory to current file path
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    #check for old output and create output folder
    outputDir = os.path.abspath("./Output")
    os.makedirs(outputDir, exist_ok = False)

    #load original excel file
    studyDict = dict()
    toProcess = []
    inputFile = os.path.abspath("./PubMed_results.xlsx")
    inputDF = pd.read_excel(inputFile).dropna(how="all")
    stats["Num_papers_assuming_duplicates_already_filtered"] = len(inputDF)
    
    #parse original excel file
    for index, row in tqdm(inputDF.iterrows(), total=len(inputDF), desc="Parsing Data", leave=True) :
        #get year
        yearKeyToLookFor = "pubDate"
        year = row[yearKeyToLookFor]
        if(type(year) != str):
            continue #filter no year
        
        year = json.loads(year)
        if("Year" not in year):
            continue #filter no year

        year=int(year["Year"])
        if(year<1950 or year>2025):
            raise Exception(f"Unexpected year val {year}")

        # get abstract
        abstract = str(row["Abstract"])
        if(abstract.strip() == "" or abstract.strip() == "nan"):
            continue #filter no abstract
        abstract = getWords(abstract,filterNums,wordsWeDontWant)
        
        #prepare output
        if year not in studyDict:
            studyDict[year] = [dict(),0] #[word dict, number of studies for that year]
        
        #prepare input
        toProcess.append({"year":year,
                       "words":abstract
                       })

    stats["num_papers_after_filter_no_year_or_no_abstract"] = len(toProcess)

    #count statistics
    for study in tqdm(toProcess,desc="Calculating statistics", leave=True) :
        yearArr = studyDict[study["year"]]
        yearDict = yearArr[0]
        yearArr[1] = yearArr[1]+1
        wordsFoundInCurrentStudy = set()
        currentWordlist = study["words"]
        for word in currentWordlist:
            #filter only words we want
            if wordsWeWant is not None and (word not in wordsWeWant):
                continue

            #word already found in year
            if word in yearDict:
                yearDict[word][0] = yearDict[word][0]+1
            else:
                yearDict[word] = [1,[],0] #[word count, list of percent of word in respective text,num studies in year mentioning word]
            
            #word not already found in block
            if(word not in wordsFoundInCurrentStudy):
                #percent of word in respective text
                wordsFoundInCurrentStudy.add(word)
                percentOfWord = 100.0*currentWordlist.count(word)/len(currentWordlist)
                yearDict[word][1].append(percentOfWord)
                #count num studies in year mentioning word
                yearDict[word][2]+=1
    
    
    #format data
    colTitles = ["word","number of mentions","Avg percent of mentions per study","percent of studies in year mentioning word"]
    colsPerYear = len(colTitles)
    #count max words
    maxWords = 0
    for yearVal in studyDict.values():
        maxWords = max(maxWords,len(yearVal[0]))
    
    shape = (maxWords+2,colsPerYear*len(studyDict))
    output =np.full(shape, "", dtype="object", order='C')

    sortedYears = sorted(studyDict.items(), key=lambda item: int(item[0]))
    for yearInd,(yearKey,yearValArr) in tqdm(enumerate(sortedYears), total = len(studyDict), desc="Formating data", leave=True):
        yearVal = yearValArr[0]
        #titles
        col = yearInd*colsPerYear
        output[0,col] = yearKey
        output[0,col+1] = "Num studies:"+str(yearValArr[1])
        output[1,col:col+colsPerYear]=colTitles

        #values
        sortedWords = sorted(yearVal.items(), key=lambda item: item[1][0],reverse =True)
        for row,(wordKey,wordVal) in enumerate(sortedWords):
            #for average, divide by number of studies in group (not len(wordVal[1]) since wordVal[1] has no entries of 0%)
            output[row+2,col:col+colsPerYear]=[wordKey,wordVal[0],str(sum(wordVal[1])/yearValArr[1])+"%",str(100*wordVal[2]/yearValArr[1])+"%"]

    #save the excel sheet with name of status
    with open(os.path.join(outputDir,'wordcount.csv'), 'w', newline='', encoding="utf-8-sig") as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(output.tolist())
    
    # write other stats
    with open(os.path.join(outputDir,"otherData.txt"), 'w') as f:
        f.writelines([json.dumps(stats, indent=4),])
    
    print("Done:",time.time()-startTime)

if __name__ == "__main__":
    main()



