# Pubmed Urology Database Word Counter

Data extraction code based on: [TLDWTutorials/PubmedAPI](https://github.com/TLDWTutorials/PubmedAPI)

Script to analyze word usage from the pubmed database. The keyword used was `("Urology"[MeSH Terms] OR "Urology"[All Fields])`

Expected outputs are given in the "Output" folder for convenience.
If you wish to filter for specific words, change the "wordsWeWant" variable in databaseWordCounter.py, then rerun(examples given in the comments on that line).
If you wish to rerun the program, follow the instructions below.

To run:

- Create an apiKey.py file where you set ([how to get api key](https://support.nlm.nih.gov/knowledgebase/article/KA-05317/en-us))

```
apiKey = "your api key as a string"
email = "your email as a string"
```

- extract ctg-studies.json.zip into a folder called "ctg-studies"
- Delete the "Output" folder
- Install python 3.10.9 (https://www.python.org/).
- Then, in the terminal, run

```
cd <path where you checked out this repository>
python -m pip install pandas==1.5.2 numpy==1.24.1 tqdm==4.64.1 bio==1.7.1 openpyxl==3.1.5
python databaseWordCounter.py
```

The results will appear in a folder called "Output"

You can also get some extra data needed for the study into the console using

```
python otherDataFromStudies.py
```

and the outputs will appear under "Output/otherData"
