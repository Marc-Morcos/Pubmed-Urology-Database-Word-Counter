#based on https://github.com/TLDWTutorials/PubmedAPI/blob/main/pubmed_api_in_python_2024.py
import pandas as pd
import json
from Bio import Entrez
from apiKey import apiKey,email
from tqdm import tqdm
import time

# what to do on Entrez exception, e is exception
def errorHandle(e):
    # auto retry on internal server error
    if("Status: 500" in str(e)):
        print(e)
        print("Retrying")
        time.sleep(Entrez.sleep_between_tries)
        return

    # else wait for user on error
    print(e)
    print("Press enter to retry")
    input()

# API key, allows 10 requests per second (without, its 3)
Entrez.api_key = apiKey
Entrez.email = email

# retry in case of error
Entrez.max_tries = 15
Entrez.sleep_between_tries = 15

full_query = '("Urology"[MeSH Terms] OR "Urology"[All Fields])'

# Get IDs to process (matching query)
# Get IDs per Month to avoid hitting 9999 limit
id_list = []
startYear = 1950
endYear = 2025
maxStudies = 9999 # imposed by API

# loop through all months in year range individually
for year in tqdm(range(startYear,endYear+1),desc="Getting pmids",leave=True):
    for month in range(1,13):

        while True: #pause, wait for user, and retry on error
            try:
                monthQuery = full_query + f' AND ("{year}/{month}:{year}/{month}[pdat])'

                # make sure its not too many studies
                handle = Entrez.esearch(db='pubmed',
                                rettype='count',
                                term=monthQuery)
                totalStudies = int(Entrez.read(handle)['Count'])
                if(totalStudies >= maxStudies):
                    raise Exception(f"Too many studies in month! {year}/{month} num:{totalStudies}")

                # get study ids
                handle = Entrez.esearch(db='pubmed', retmax=maxStudies, term=monthQuery)
                record = Entrez.read(handle)
                id_list += record['IdList']

                # make sure we have ALL studies
                numStudiesMonth = len(record['IdList'])
                if(numStudiesMonth != totalStudies):
                    raise Exception(f"only have {numStudiesMonth}/{totalStudies} studies")
                
                break #next iteration
            except Exception as e:
                errorHandle(e)
                pass #retry iteration

# Remove duplicates by pmid
id_list = list(set(id_list))

# DataFrame to store the extracted data
df = pd.DataFrame(columns=['PMID', 'Title', 'Abstract', 'Authors', 'Journal', 'Keywords', 'URL', 'Affiliations','pubDate','fullRecord'])

# Fetch information for each record in the id_list
for pmid in tqdm(id_list,desc="Getting individual article data",leave=True):
    while True: #pause, wait for user, and retry on error
        try:
            handle = Entrez.efetch(db='pubmed', id=pmid, retmode='xml')
            records = Entrez.read(handle)
            break #next iteration
        except Exception as e:
            errorHandle(e)
            pass #retry iteration

    # Process each PubMed article in the response
    for record in records['PubmedArticle']:
        # Print the record in a formatted JSON style
        # print(json.dumps(record, indent=4, default=str))  # default=str handles types JSON can't serialize like datetime
        title = record['MedlineCitation']['Article']['ArticleTitle']
        abstract = ' '.join(record['MedlineCitation']['Article']['Abstract']['AbstractText']) if 'Abstract' in record['MedlineCitation']['Article'] and 'AbstractText' in record['MedlineCitation']['Article']['Abstract'] else ''
        authors = ', '.join(author.get('LastName', '') + ' ' + author.get('ForeName', '') for author in record['MedlineCitation']['Article']['AuthorList'])
        
        affiliations = []
        for author in record['MedlineCitation']['Article']['AuthorList']:
            if 'AffiliationInfo' in author and author['AffiliationInfo']:
                affiliations.append(author['AffiliationInfo'][0]['Affiliation'])
        affiliations = '; '.join(set(affiliations))

        journal = record['MedlineCitation']['Article']['Journal']['Title']
        keywords = ', '.join(keyword['DescriptorName'] for keyword in record['MedlineCitation']['MeshHeadingList']) if 'MeshHeadingList' in record['MedlineCitation'] else ''
        url = f"https://www.ncbi.nlm.nih.gov/pubmed/{pmid}"

        pubDate = json.dumps(record['MedlineCitation']['Article']['Journal']["JournalIssue"]["PubDate"])

        new_row = pd.DataFrame({
            'PMID': [pmid],
            'Title': [title],
            'Abstract': [abstract],
            'Authors': [authors],
            'Journal': [journal],
            'Keywords': [keywords],
            'URL': [url],
            'Affiliations': [affiliations],
            'pubDate': [pubDate],
            'fullRecord': [json.dumps(record)]
        })

        df = pd.concat([df, new_row], ignore_index=True)

# Save DataFrame to an Excel file
df.to_excel('PubMed_results.xlsx', index=False)