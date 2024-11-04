# Pubmed Urology Database Word Counter

Data extraction code based on: [TLDWTutorials/PubmedAPI](https://github.com/TLDWTutorials/PubmedAPI)

Script to analyze word usage from the pubmed database. The keyword used was `("Urology"[MeSH Terms] OR "Urology"[All Fields])`, plus some date filtering between 1950 and 2025 (up to current day)

Expected outputs are given in the "Output" folder for convenience.
If you wish to filter for specific words, change the "wordsWeWant" variable in databaseWordCounter.py, then rerun(examples given in the comments on that line). You can also change "wordsToFilterList" in wordsToFilterList.py to filter out words.
If you wish to rerun the program, follow the instructions below.

To run:

- Create an apiKey.py file where you set: ([how to get api key](https://support.nlm.nih.gov/knowledgebase/article/KA-05317/en-us))

```
apiKey = "your api key as a string"
email = "your email as a string"
```

- Install python 3.10.9 (https://www.python.org/).
- Then, in the terminal, run
  `python -m pip install pandas==1.5.2 numpy==1.24.1 tqdm==4.64.1 bio==1.7.1 openpyxl==3.1.5`

To download the data, run `python downloadData.py`
This will take hours and results will appear in an excel sheet called `PubMed_results.xlsx`

To process the data, run `python databaseWordCounter.py` (If there is an `Output` folder, you must delete it before starting)

The results will appear in a folder called `Output`
