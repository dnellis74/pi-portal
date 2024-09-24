# Air Quality Policy Search Engine

This document outlines the approach and requirements for building a smart search engine using AWS Kendra, specifically tailored for air quality policies across 60+ states and air districts. This search engine will facilitate targeted searches, filtering, and enrichment of documents from state and district agencies responsible for air quality management.

## 1. Data Sources and Naming Convention

We will use AWS Kendra’s ability to handle multiple data sources, with each state or air district treated as a separate data source. The naming convention will follow a standard format:

- **Format**: `[State]-[district (if applicable)]-[agency-name]`
- **Example**: `Colorado-dept-public-health-environment`, `California-south coast-air-quality-management-district`

This allows us to map the documents accurately and easily create filters by state/district.

## 2. Web Crawling Strategy

Each data source will have a defined set of domains to be crawled for relevant policy documents. We will target primary domains where valuable air quality policy documents are most likely to reside.

### Examples of Targeted Scraping:
- **SCAQMD**: Focus on the single domain we have right now (https://www.aqmd.gov/docs).
- **Colorado**: 29 different domains identified for crawling.

The goal is to remain under Kendra Developer Edition's limit of **10,000 documents** or 166 docs per 60 state/distric, so strategic domain targeting is crucial and filtering on doc type to dowqnload are key.

## 3. Document Type Targeting

For each state or air district, we will leverage Kendra’s advanced scraping features to only include or exclude specific document types, optimizing the search results and staying under document limits.

- **Inclusions**: Specific keywords or phrases (e.g., “.pdf” in the subdomains for relevant PDFs).

We will ensure the scraping rules are state-specific, as document formats and types can vary widely across jurisdictions.

- **Efficient LDAR Report Targeting**

Given the high volume of irrelevant LDAR facility reports (over 1000, or 10% of the space we are alotted in dev Kendra), we will directly supply Kendra with the raw OnBase links to the relevant LDAR Annual Reports instead of crawling the entire domain. This approach saves document space for other critical documents across the 59 other states and ensures only the most pertinent Colorado LDAR reports are indexed. 


## 4. Filter by State and Document Enrichment

Using the separate data sources for each state, we will build a filter that allows users to narrow down searches by state or district easily. This will use the database name as the filter Additionally, we will use document enrichment features to create other filter options such as:

- **Document type**: (e.g., regulations, permits, etc.)
- **Publication year**: Helps refine results to the most relevant or up-to-date documents.
  
Enrichment will also allow us to capture metadata like effective dates, expiration dates, and policy keywords.

## 5. Thesaurus for Acronyms

To improve search functionality, we will build a thesaurus of commonly used acronyms in air quality policy. This thesaurus will map abbreviations to their full terms to enhance search accuracy.

- **Example**: `LDAR = Leak Detection and Repair`, `PM2.5 = Particulate Matter 2.5 microns or less`

## 6. FAQ and Glossary of Document Types

An FAQ section will be added to guide users on common document types and questions related to the air quality policy documents.

- **Common Document Types**: Define the difference between permits, regulations, environmental impact assessments, etc.
- **Search Tips**: Best practices for finding specific types of documents.
  
This helps users navigate the search engine more effectively.

---

## Additional Input:

1. **Document Volume Management**: One way to manage the 10k document limit could be to rank and prioritize documents by relevance (date, importance, or policy type). You might consider batching uploads in order of importance for each state/district.
   
2. **Custom Ranking**: You can add custom ranking when users search. For example, prioritize newer documents or give more weight to documents with more citations/references, etc.

3. **Data Integrity**: Make sure to set up automatic crawling updates or checks so new documents don’t slip through the cracks.

4. **Acronym Mapping Expansion**: Since air quality has a ton of jargon, it might be useful to expand the thesaurus over time based on user searches. You could add terms dynamically as users interact with the engine.

