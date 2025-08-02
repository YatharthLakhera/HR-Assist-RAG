# Prompts
QUERY_REWRITE_PROMPT_HARD_CRITERIA = """
You are an expert at transforming detailed, unstructured professional experience descriptions into precise, structured search criteria. For a given user query describing a professional profile, extract and organize key qualifications and experience into two categories:

Hard Criteria: Mandatory, non-negotiable qualifications (e.g., degrees, years of experience, professional certifications, specific roles).

Follow these guidelines strictly:

Input: Only the natural language user query describing the candidate’s profile.
Output: Two sections labeled Hard Criteria and Soft Criteria with corresponding numbered lists of criteria.

Focus on creating concise, specific, and realistic search terms grounded in the description.
Use quantifiable experience where possible (e.g., "3+ years," "PhD degree from a top United States university").
Keep criteria relevant and aligned with common search filters (degree, experience, skills, certifications, domain expertise).
Avoid redundancy between Hard and Soft criteria.
Be consistent in formatting as in the examples.

Remember: Hard criteria should be concrete, essential qualifications; soft criteria should capture valuable but flexible skills, experiences, or attributes.
Important : Convert country name to full names like U.S. = United States

*Example 1:*

<user_query_start>
Seasoned attorney with a JD from a top U.S. law school and over three years of legal practice, specializing in corporate tax structuring and compliance. Has represented clients in IRS audits and authored legal opinions on federal tax code matters.
</user_query_end>

<response_start>
Hard Criteria:
JD degree from an accredited United States law school
3+ years of experience practicing law
</response_end>

*Example 2*

<user_query_start>
U.S. trained physician with over two years of experience as a general practitioner, focused on chronic care management, wellness screenings, and outpatient diagnostics. Skilled in telemedicine and patient education.
</user_query_end>

<response_start>
Hard Criteria:
1. MD degree from a top United States medical school
2. 2+ years of clinical practice experience in the United States.
3. Experience working as a General Practitioner (GP)
</response_end>


*Example 3*

<user_query_start>
Radiologist with an MD from India and several years of experience reading CT and MRI scans. Well-versed in diagnostic workflows and has worked on projects involving AI-assisted image analysis.
</user_query_end>

<response_start>
Hard Criteria:
MD degree from a medical school in the United States or India
</response_end>

NOTE : Hard criteria is mandatory to be part of the new query and if possible it should have soft criteria

Now, convert the following user query into structured search criteria(having both hard criteria and soft criteria):
"""


QUERY_REWRITE_PROMPT_SOFT_CRITERIA = """
You are an expert at transforming detailed, unstructured professional experience descriptions into precise, structured search criteria. For a given user query describing a professional profile, extract and organize key qualifications and experience into two categories:

Hard Criteria: Mandatory, non-negotiable qualifications (e.g., degrees, years of experience, professional certifications, specific roles).
Soft Criteria: Preferred, complementary experience or skills that enhance but do not strictly determine eligibility.

Follow these guidelines strictly:

Input: Only the natural language user query describing the candidate’s profile.
Output: Two sections labeled Hard Criteria and Soft Criteria with corresponding numbered lists of criteria.

Focus on creating concise, specific, and realistic search terms grounded in the description.
Use quantifiable experience where possible (e.g., "3+ years," "PhD degree from a top United States university").
Keep criteria relevant and aligned with common search filters (degree, experience, skills, certifications, domain expertise).
Avoid redundancy between Hard and Soft criteria.
Be consistent in formatting as in the examples.

Remember: Hard criteria should be concrete, essential qualifications; soft criteria should capture valuable but flexible skills, experiences, or attributes.

*Example 1:*

<user_query_start>
Seasoned attorney with a JD from a top U.S. law school and over three years of legal practice, specializing in corporate tax structuring and compliance. Has represented clients in IRS audits and authored legal opinions on federal tax code matters.
</user_query_end>

<response_start>

Soft Criteria:
Experience advising clients on tax implications of corporate or financial transactions
Experience handling IRS audits, disputes, or regulatory inquiries
Experience drafting legal opinions or filings related to federal and state tax compliance
</response_end>

*Example 2*

<user_query_start>
U.S. trained physician with over two years of experience as a general practitioner, focused on chronic care management, wellness screenings, and outpatient diagnostics. Skilled in telemedicine and patient education.
</user_query_end>

<response_start>

Soft Criteria:
1. Familiarity with EHR systems and managing high patient volumes in outpatient or family medicine settings
2. Comfort with telemedicine consultations, patient triage, and interdisciplinary coordination
</response_end>


*Example 3*

<user_query_start>
Radiologist with an MD from India and several years of experience reading CT and MRI scans. Well-versed in diagnostic workflows and has worked on projects involving AI-assisted image analysis.
</user_query_end>

<response_start>
Soft Criteria:
Board certification in Radiology (ABR, FRCR, or equivalent) or comparable credential
3+ years of experience interpreting X-ray, CT, MRI, ultrasound, or nuclear medicine studies
Expertise in radiology reporting, diagnostic protocols, differential diagnosis, or AI applications in medical imaging
</response_end>

NOTE : Hard criteria is mandatory to be part of the new query and if possible it should have soft criteria

Now, convert the following user query into structured search criteria(having both hard criteria and soft criteria):
"""

# RE_RANKING_PROMPT = (
#         "Given the following query:\n{0}\n\n"
#         "Candidate should be ranked higher if"
#         "Critical : Rank the candidate on below first on hard criteria. If the candidate doesn't meet any of the hard criteria means they are not good match. Also the candidate experience and eduction should match the country in the query based on the requirement"
#         "Current country of the candidate can be different from the country of education and companies the candidate’s has attended so be careful that you don't mix them up when searching"
#         "1. If they have the required degress/qualifications as asked in the query"
#         "2. If asked for candidate to be from top universities, companies, etc in specific country - Check if the candidate’s universities, companies, etc are in the specific country or not. Rate it based on that"
#         "3. If they have required experience on the roles asked for in the query"
#         "4. If they have the skills which are asked in the query"
#         "5. If they are from the country asked in the query"
#         "6. If they have experience and eduction from good universities and companies in the country asked in the query"
#         "7. If they have relevant awardsAndCertifications which can help in the role"
#         "8. If they have education from good universities/schools which are in-line to the role"
#         "Note : The weightage is based on the above priority, 1 being highest"
#         "What to deprioritize"
#         "- if the candidate is from top universities or companies but not in the country of interest"
#         "(i.e. if the search of for top USA university then candidate doesn't qualifies if they have a non-US university)"
#         "- if the candidate doesn't have experience in the exact field criteria for the role(i.e. on duty doctor when search is for General Practitioner)"
#         "Documents:\n{1}"
#         "Output should be list of all document in json format as shared here : {2}"
#         "*Important Note* : If a candidate doesn't meet any of the hard criterias, ranking_score should be less than 20. And return list of all {3} profiles with scores"
#     )

# ++++++ CHAT GPT ++++++
# RE_RANKING_PROMPT = '''
# You are an expert evaluator tasked with re-ranking candidate profiles based on the following user query:

# USER QUERY:
# {0}

# You will receive a list of candidate profiles. Each profile contains education, work experience, country information, skills, and other metadata.

# INSTRUCTIONS:
# Evaluate each candidate **strictly** according to the criteria below. Assign a ranking_score between 0 and 100.

# ====================
# **HARD CRITERIA** (must-have, critical requirements):
# If a candidate fails **any** of these, their ranking_score MUST be 0 — no exceptions.
# 1. Required degrees/qualifications as specified in the query.
# 2. If the query asks for candidates from **top universities or companies in a specific country**, the candidate must have studied or worked at such institutions **in that country**.
# 3. Must have required experience in the specific roles or fields mentioned in the query.
# 4. Must possess all explicitly mentioned skills in the query.
# 5. Candidate must be from or have experience/education in the country specified in the query.

# IMPORTANT NOTE: Do not confuse the **current country** of the candidate with the **location of their education or work experience**. Evaluate university and company locations independently of current residence.

# ====================
# **SOFT CRITERIA** (nice-to-have, improves score if present):
# These only matter **after** hard criteria are met. They help differentiate between valid candidates.
# - Experience and education from prestigious institutions in the required country.
# - Relevant awards and certifications that improve qualification for the role.
# - Longer or more specialized experience in the relevant domain.

# ====================
# **DEPRIORITIZATION RULES** (must lower score):
# - Candidate studied or worked at top institutions **but not in the country specified** — this is not acceptable if the query asked for a specific country.
# - Candidate lacks direct experience in the specific field mentioned (e.g. worked as on-duty doctor but query asks for General Practitioner).

# ====================
# **OUTPUT FORMAT:**
# Return a JSON object with the following schema:
# {2}

# For each candidate, include:
# - _id
# - ranking_score (0-100)
# - detailed_reason_for_ranking (explain clearly why score was assigned, referencing specific hard and soft criteria)

# *If a candidate fails any hard criteria, their score must be under 20.*
# Rank and return all {3} profiles.

# ====================
# CANDIDATE PROFILES:
# {1}
# '''
# ++++++ CHAT GPT ++++++


# ++++++ GEMINI ++++++
# def get_re_ranking_prompt(query: str, candidate_profiles: list) -> str:
#     candidate_profiles_str = "\n\n".join(candidate_profiles)
#     return (
#     "Objective: Re-rank a list of candidate profiles based on a user query. Your scoring MUST strictly follow a two-stage process:\n\n"
#     "Stage 1: Hard Criteria (Pass/Fail)\n"
#     "A candidate is a viable match ONLY IF they meet ALL of the following hard criteria. If a candidate fails to meet even one of these criteria, their ranking_score MUST be 0.\n"
#     "Hard Criteria Checklist:\n"
#     "1. Degrees/Qualifications: Does the candidate have the required degrees or qualifications from the user query?\n"
#     "2. Relevant Roles: Do they have the required experience in the specific roles mentioned in the query?\n"
#     "3. Country of Interest: Is the candidate from the country specified in the query? (The candidate's current country, country of education, and company locations can be different, so verify this carefully).\n"
#     "4. Top Institutions in Country: If the query asks for top universities or companies, are they from top institutions in the specified country? (e.g., if the search is for a top US university, a top non-US university does not qualify).\n\n"
#     "Stage 2: Soft Criteria (Scoring 20-100)\n"
#     "For candidates who have passed all hard criteria, use the following soft criteria to determine a precise ranking_score between 20 and 100. Higher scores indicate a better overall fit.\n"
#     "Soft Criteria Checklist:\n"
#     "1. Education & Experience: Does the candidate have experience and education from reputable companies and universities in the country of interest?\n"
#     "2. General Skills: Do they possess the general skills and qualifications asked for in the query?\n"
#     "3. Awards/Certifications: Do they have relevant awards or certifications that would be beneficial for the role?\n"
#     "4. Reputation of Institutions: Did they attend good universities or companies that are in-line with the role, regardless of country?\n\n"
#     "Deprioritization Rules:\n"
#     "- Do not give a high score to a candidate from a top university or company if that institution is not in the country of interest.\n"
#     "- If a candidate's experience is not in the exact field of the role (e.g., a general practitioner search for an on-duty doctor), it should be a lower priority.\n\n"
#     "Input:\n"
#     f"User Query:\n{query}\n"
#     f"Candidate Profiles (Documents):\n{candidate_profiles_str}\n\n"
#     "Output Instructions:\n"
#     f"Return a list of all {len(candidate_profiles)} profiles with their scores. The output must be in the following JSON schema. For the detailed_reason_for_ranking, clearly state which hard criteria were met or failed, and how the soft criteria influenced the final score.\n"
#     "Schema:\n "
#     '''
#     {
#       "results": [
#         {
#           "_id": "<document_id>",
#           "ranking_score": 85,
#           "hard_constraints_passed": [
#             "Required degree/qualification",
#             "Geographic requirement",
#             "Required role experience",
#             "Required skills"
#           ],
#           "hard_constraints_failed": [
#             "Relevant awards/certifications",
#             "Education alignment with role requirements"
#           ],
#           "detailed_reason_for_ranking": "Candidate meets all primary hard constraints (degree, geography, role experience, skills). They lack the specified awards/certifications and have education from institutions slightly outside the role’s core alignment, yielding a strong but not perfect match."
#         },
#         {
#           "_id": "<document_id>",
#           "ranking_score": 15,
#           "hard_constraints_passed": [
#             "Required skills"
#           ],
#           "hard_constraints_failed": [
#             "Required degree/qualification",
#             "Geographic requirement",
#             "Required role experience",
#             "Candidate’s current country"
#           ],
#           "detailed_reason_for_ranking": "Candidate fails multiple mandatory hard constraints: missing the required degree, not educated in the specified country, lacks role-specific experience, and is not currently based in the target country. Per the strict enforcement rules, score is set below 20."
#         },
#         {
#           "_id": "<document_id>",
#           "ranking_score": 45,
#           "hard_constraints_passed": [
#             "Required degree/qualification",
#             "Geographic requirement",
#             "Required role experience",
#             "Required skills",
#             "Candidate’s current country"
#           ],
#           "hard_constraints_failed": [],
#           "detailed_reason_for_ranking": "Candidate satisfies all hard constraints. Soft-criteria analysis yields a moderate match based on average institution prestige and solid but not exceptional career progression."
#         }
#       ]
#     }\n
#     '''
#     )
# ++++++ GEMINI ++++++

# ++++++ Perplexity ++++++
def get_re_ranking_prompt(query: str, candidate_profiles: list) -> str:
    candidate_profiles_str = "\n\n".join(candidate_profiles)
    return (
        "MANDATORY RE-RANKING & CONSTRAINT CHECKING SYSTEM\n"
        "You MUST rank candidate profiles against the user query STRICTLY as follows.\n\n"
        "== PHASE 1: HARD CONSTRAINTS (MANDATORY, PASS/FAIL) ==\n"
        "For EACH candidate, EVALUATE the following hard criteria one by one. "
        "IF the candidate fails ANY single hard criterion, stop further evaluation: "
        "immediately assign a ranking_score of 0-15 (based on number and severity of failures), and explain exactly why in the output.\n"
        "HARDCONSTRAINTS:\n"
        "1. Required Degree/Qualification: Does the candidate hold the specific degrees or qualifications listed in the query?\n"
        "2. Role Experience: Do they have explicit experience in the roles (titles or responsibilities) stated in the query?\n"
        "3. Country of Interest: Are they from the country specified in the query? (Be careful: Candidate's current location, country of education, and job history can differ. Only pass this constraint if the right kind of match exists.)\n"
        "4. Top Institutions in Country: If the query requires a 'top' university or employer in a specific country, "
        "do all relevant degree(s)/employment records come from top institutions in that country? (E.g., Top US University ≠ Top UK University)\n"
        "5. Any additional 'must have' (explicit hard) requirements present in the query.\n"
        "If any of the above are not met, the candidate is NOT a viable match—score as FAIL.\n\n"
        "== PHASE 2: SOFT CRITERIA (SCORE ONLY IF ALL HARD CRITERIA PASSED) ==\n"
        "If a candidate passes ALL hard constraints,"
        "assign a ranking_score between 20 and 100 according to their fit for these soft criteria:\n"
        "- Education and experience from especially good institutions/companies within the country of interest\n"
        "- General and role-specific skills as per the query\n"
        "- Relevant awards or certifications\n"
        "- Quality and depth of career progression or prior impact\n\n"
        "== DEPRIORITIZATION RULES ==\n"
        "- NEVER assign a high score to a candidate from a top institution or employer if it is not in the country of interest.\n"
        "- If the candidate's experience is not in the exact required field, deprioritize appropriately even if all hard criteria are met.\n\n"
        "== OUTPUT FORMAT & EXPLANATION REQUIREMENT ==\n"
        f"User Query:\n{query}\n\n"
        f"Candidate Profiles:\n{candidate_profiles_str}\n\n"
        "Return the re-ranked list of all "
        f"{len(candidate_profiles)} profiles with their scores. "
        "For each candidate, clearly list:\n"
        "- Which hard constraints were PASSED, which were FAILED (use explicit checklist)\n"
        "- How soft criteria influenced the final score (if applicable)\n"
        "- Provide a detailed_reason_for_ranking that accounts for BOTH constraint checking and soft criteria.\n"
        "Use this output schema (update with each candidate's real results):\n"
        '''
        {
          "results": [
            {
              "_id": "<document_id>", -- **this is unique so its critical to keep this information intact**
              "ranking_score": 85,
              "hard_constraints_passed": [
                "Required degree/qualification",
                "Geographic requirement",
                "Required role experience",
                "Required skills"
              ],
              "hard_constraints_failed": [
                "Relevant awards/certifications",
                "Education alignment with role requirements"
              ],
              "detailed_reason_for_ranking": "Candidate meets all primary hard constraints (degree, geography, role experience, skills). They lack the specified awards/certifications and have education from institutions slightly outside the role’s core alignment, yielding a strong but not perfect match."
            }
          ]
        }
        '''
    )
# ++++++ Perplexity ++++++

FILTER_EXTRACTION_PROMPT = (
    "From the following search query, extract JSON with keys 'country' (string) "
    "based on context, or leave them blank/null if not stated."
    "Query in most cases will have a country present in it so don't miss it. It can be abbreviated so be though in checking if country is there."
    "Its critical information and we don't want to miss this if present"
    "Example output: "
    "{{\"country\": \"United States\"}}\n "
    "If country is not available, return output as -> {}"
    "Also if a country in description is USA or U.S -> use United States as country in filters and do this for others as well"
    "Query: "
)