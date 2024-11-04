import re
import csv
import os
import pandas as pd
import numpy as np
import time
from tqdm import tqdm
import json
from wordsToFilterList import wordsToFilterList

#get list of words
def getWords(text, filterNums, wordsWeDontWant = ()):
    #remove everything but words, digits, whitespace, apostrophe, and dash (replace with space)
    text = re.sub(r'[^\w\d\s\'-]+', ' ', text)

    #lowercase
    text = text.lower()

    #split into words (removes whitespace)
    text=text.split()

    newText = []
    for word in text:
        # get rid of 's at END of words
        word = re.sub("'s$", '', word)

        # remove apostrophes or dashes at begining/end
        word = word.strip("-'")

        # remove one (or zero (can happen due to previous filters)) letter words
        if len(word) <= 1:
            continue

        # get rid of numbers or numbers seperated by dashes
        if(filterNums and word.isnumeric() or word.replace('-','').isnumeric()):
            continue

        # get rid of words we dont want
        if(word in wordsWeDontWant):
            continue

        newText.append(word)

    return newText

# output all words with their year beside them
def outputYearWord(toProcess,wordsWeWant,outputDir):
    output = [["year","word"]]
    
    #count statistics
    for study in tqdm(toProcess,desc="Calculating statistics", leave=True) :
        currentWordlist = study["words"]
        for word in currentWordlist:
            #filter only words we want
            if wordsWeWant is not None and (word not in wordsWeWant):
                continue

            output.append([study["year"],word])

    print("Saving raw_word_year.csv")
    #save the excel sheet with name of status
    with open(os.path.join(outputDir,'raw_word_year.csv'), 'w', newline='', encoding="utf-8-sig") as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(output)

#populate study dict for pipeline 1
def getStudyDictForPipeline1(toProcess,wordsWeWant):
    class YearEntry:
        def __init__(self):
            self.wordDict = dict()
            self.numStudies = 0

    class WordEntry:
        def __init__(self):
            self.totalNumMentions = 0
            self.listOfPercentOfStudy = []
            self.numStudiesMentioning = 0

    studyDict = dict()

    #count statistics
    for study in tqdm(toProcess,desc="Calculating statistics", leave=True) :
        year = study["year"]

        if year not in studyDict:
            studyDict[year] = YearEntry()

        yearArr = studyDict[year]
        yearDict = yearArr.wordDict
        yearArr.numStudies = yearArr.numStudies+1
        wordsFoundInCurrentStudy = set()
        currentWordlist = study["words"]
        for word in currentWordlist:
            #filter only words we want
            if wordsWeWant is not None and (word not in wordsWeWant):
                continue

            #word already found in year
            if word in yearDict:
                yearDict[word].totalNumMentions = yearDict[word].totalNumMentions+ 1
            else:
                yearDict[word] = WordEntry()
                yearDict[word].totalNumMentions = 1
                
            
            #word not already found in block
            if(word not in wordsFoundInCurrentStudy):
                #percent of word in respective text
                wordsFoundInCurrentStudy.add(word)
                percentOfWord = 100.0*currentWordlist.count(word)/len(currentWordlist)
                yearDict[word].listOfPercentOfStudy.append(percentOfWord)
                #count num studies in year mentioning word
                yearDict[word].numStudiesMentioning = yearDict[word].numStudiesMentioning+1
    
    return studyDict

# pipeline for output
def pipeline1(toProcess,wordsWeWant,outputDir):

    studyDict = getStudyDictForPipeline1(toProcess,wordsWeWant)
    
    #format data
    colTitles = ["word","number of mentions","Avg percent of mentions per study","percent of studies in year mentioning word"]
    colsPerYear = len(colTitles)
    #count max words
    maxWords = 0
    for yearVal in studyDict.values():
        maxWords = max(maxWords,len(yearVal.wordDict))
    
    shape = (maxWords+2,colsPerYear*len(studyDict))
    output =np.full(shape, "", dtype="object", order='C')

    sortedYears = sorted(studyDict.items(), key=lambda item: int(item[0]))
    for yearInd,(yearKey,yearValArr) in tqdm(enumerate(sortedYears), total = len(studyDict), desc="Formating data", leave=True):
        yearVal = yearValArr.wordDict
        #titles
        col = yearInd*colsPerYear
        output[0,col] = yearKey
        output[0,col+1] = "Num studies:"+str(yearValArr.numStudies)
        output[1,col:col+colsPerYear]=colTitles

        #values
        sortedWords = sorted(yearVal.items(), key=lambda item: item[1].totalNumMentions,reverse =True)
        for row,(wordKey,wordVal) in enumerate(sortedWords):
            #for average, divide by number of studies in group (not len(wordVal.listOfPercentOfStudy) since wordVal.listOfPercentOfStudy has no entries of 0%)
            # ["word","number of mentions","Avg percent of mentions per study","percent of studies in year mentioning word"]
            avgPercentMentionsPerStudy = str(sum(wordVal.listOfPercentOfStudy)/yearValArr.numStudies)+"%"
            percentStudiesMentioningWord = str(100*wordVal.numStudiesMentioning/yearValArr.numStudies)+"%"
            output[row+2,col:col+colsPerYear]=[wordKey,wordVal.totalNumMentions,avgPercentMentionsPerStudy,percentStudiesMentioningWord]

    #save the excel sheet with name of status
    with open(os.path.join(outputDir,'wordcount.csv'), 'w', newline='', encoding="utf-8-sig") as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(output.tolist())

def main():
    stats = dict() #used for other notes

    startTime = time.time()
    print("Starting")

    # word filters
    wordsWeWant = None #"Depression,Anxiety,esteem,Schizophrenia,Borderline personality disorder,stress,personality,emasculation,humiliation,isolation,loneliness,frustration" #None
    wordsWeDontWant = wordsToFilterList
    filterNums = True #if true, filter out words that are entirely numbers
    yearWordMode = False # if true, outputs each word accompanied by year it showed up in

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
        
        #prepare input
        toProcess.append({"year":year,
                       "words":abstract
                       })

    stats["num_papers_after_filter_no_year_or_no_abstract"] = len(toProcess)

    if(yearWordMode):
        outputYearWord(toProcess,wordsWeWant,outputDir)
    
    pipeline1(toProcess,wordsWeWant,outputDir)

    # write other stats
    with open(os.path.join(outputDir,"otherData.txt"), 'w') as f:
        f.writelines([json.dumps(stats, indent=4),])
    
    print("Done:",time.time()-startTime)

if __name__ == "__main__":
    main()



