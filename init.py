import openai
import voyageai
from qdrant_client import QdrantClient
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import os
import logging
import requests

from prompts import FILTER_EXTRACTION_PROMPT, QUERY_REWRITE_PROMPT_HARD_CRITERIA, QUERY_REWRITE_PROMPT_SOFT_CRITERIA, get_re_ranking_prompt
from schema import RE_RANK_SCHEMA, ENHANCED_RE_RANK_SCHEMA

# Your search input
# search_query = "Mathematician with a PhD from a leading U.S, specializing in statistical inference and stochastic processes. Published and experienced in both theoretical and applied research."

LOG = True

search_query = {
    "tax_lawyer": {
        "query": "Seasoned attorney with a JD from a top U.S. law school and over three years of legal practice, specializing in corporate tax structuring and compliance. Has represented clients in IRS audits and authored legal opinions on federal tax code matters.",
        "template": "tax_lawyer.yml"
    },
    "junior_corporate_lawyer": {
        "query": "Corporate lawyer with two years of experience at a top-tier international law firm, specializing in M&A support and cross-border contract negotiations. Trained at a leading European law school with additional background in international regulatory compliance.",
        "template": "junior_corporate_lawyer.yml"
    },
    "radiology": {
        "query": "Radiologist with an MD from India and several years of experience reading CT and MRI scans. Well-versed in diagnostic workflows and has worked on projects involving AI-assisted image analysis.",
        "template": "radiology.yml"
    },
    "doctor_md": {
        "query": "U.S.-trained physician with over two years of experience as a general practitioner, focused on chronic care management, wellness screenings, and outpatient diagnostics. Skilled in telemedicine and patient education.",
        "template": "doctors_md.yml"
    },
    "biology_expert": {
        "query": "Biologist with a PhD from a top U.S. university, specializing in molecular biology and gene expression",
        "template": "biology_expert.yml"
    },
    "anthropology": {
        "query": "PhD student in anthropology at a top U.S. university, focused on labor migration and cultural identity",
        "template": "anthropology.yml"
    },
    "mathematics_phd": {
        "query": "Mathematician with a PhD from a leading U.S, specializing in statistical inference and stochastic processes. Published and experienced in both theoretical and applied research.",
        "template": "mathematics_phd.yml"
    },
    "quantitative_finance": {
        "query": "MBA graduate from a top U.S. program with 3+ years of experience in quantitative finance, including roles in risk modeling and algorithmic trading at a global investment firm. Skilled in Python and financial modeling, with expertise in portfolio optimization and derivatives pricing.",
        "template": "quantitative_finance.yml"
    },
    "bankers": {
        "query": "Healthcare investment banker with over two years at a leading advisory firm, focused on M&A for multi-site provider groups and digital health companies. Currently working in a healthcare-focused growth equity fund, driving diligence and investment strategy.",
        "template": "bankers.yml"
    },
    "mechanical_engineers": {
        "query": "Mechanical engineer with over three years of experience in product development and structural design, using tools like SolidWorks and ANSYS. Led thermal system simulations and supported prototyping for electromechanical components in an industrial R&D setting.",
        "template": "mechanical_engineers.yml"
    }
}

# API keys & endpoints (replace with yours)
os.environ["OPENAI_API_KEY"] = ""
os.environ["VOYAGE_API_KEY"] = ""
QDRANT_URL = ""
QDRANT_API_KEY = ""
QDRANT_COLLECTION = ""
MONGO_URI = ""
MONGO_DB = ""
MONGO_COLLECTION = ""

# ==== OPENAI AND VOYAGE CLIENTS INIT ====
openai.api_key = os.environ["OPENAI_API_KEY"]
voyage_client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
mongo_client = MongoClient(MONGO_URI)
mongo_collection = mongo_client[MONGO_DB][MONGO_COLLECTION]

# ==== CORE FUNCTIONS ====

def get_transformed_query(query, rewrite_prompt):
    messages = [
        {"role": "system", "content": "You are an expert recruiter and search query rewriter."},
        {"role": "user", "content": f"{rewrite_prompt} {query}"},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4.1-nano",
        messages=messages,
        max_tokens=4000,
    )
    return response["choices"][0]["message"]["content"].strip()


def extract_filters(query):
    messages = [
        {"role": "system", "content": "You extract JSON filters."},
        {"role": "user", "content": FILTER_EXTRACTION_PROMPT + query},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4.1-nano",
        messages=messages,
        max_tokens=6000,
    )
    # Robust decoding
    try:
        filters_json = response["choices"][0]["message"]["content"].strip()
        filters = json.loads(filters_json)
        must = []
        if filters.get("country"):
            must.append({"key": "country", "match": {"value": filters["country"]}})
        years_filter = filters.get("yearsOfWorkExperience")
        if years_filter and isinstance(years_filter, dict):
            range_filter = {}
            if "min" in years_filter and years_filter["min"] is not None:
                range_filter["gte"] = years_filter["min"]
            if "max" in years_filter and years_filter["max"] is not None:
                range_filter["lte"] = years_filter["max"]
            if range_filter:
                must.append({"key": "yearsOfWorkExperience", "range": range_filter})
        final_filter = {"must": must} if must else {}
        return final_filter
    except Exception:
        return {}


def create_embedding(text):
    embed_response = voyage_client.embed(
        texts=[text], model="voyage-3", input_type="query"
    )
    return embed_response.embeddings[0]


def query_qdrant(embedding, filters):
    # Build Qdrant filter structure
    must = []
    if filters.get("country"):
        must.append({"key": "country", "match": {"value": filters["country"]}})
    if filters.get("yearsOfWorkExperience"):
        must.append({"key": "yearsOfWorkExperience", "range": {"gte": filters["yearsOfWorkExperience"]}})
    final_filter = {"must": must} if must else None

    result = qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=embedding,
        limit=50,
        query_filter=final_filter,
    )
    # Get (mongo_id, prestigeScore)
    id_score_pairs = []
    for point in result:
        mongo_id = point.payload.get("mongo_id")
        prestige = point.payload.get("prestigeScore", 0)
        if mongo_id:
            id_score_pairs.append((mongo_id, prestige))
    # Sort by prestige descending
    # id_score_pairs.sort(key=lambda tup: tup[1], reverse=True)
    return [pair[0] for pair in id_score_pairs]

def rerank_documents(query: str, docs_to_rerank: list) -> list:

    # Limit doc count to keep prompt small and cost effective
    # docs_to_rerank = docs[:max_docs_for_rerank]

    docs_by_id = {}
    # Create a simple summary string for each doc to feed LLM
    # Customize which fields are most relevant for your use case
    doc_summaries = []
    for idx, doc in enumerate(docs_to_rerank):
        doc_id = "doc-" + str(idx + 1)
        # doc_id = str(doc["_id"])
        docs_by_id[doc_id] = doc
        summary = {
            "_id": doc_id,
            "headline": doc.get("headline", "NA"),
            "experience": doc["experience"],
            "yearsOfWorkExperience": doc["yearsOfWorkExperience"],
            "rerankSummary": doc["rerankSummary"],
            "prestigeScore": doc["prestigeScore"],
            "skills": doc["skills"],
            "awardsAndCertifications": doc["awardsAndCertifications"],
            "education": doc["education"]
        }
        doc_summaries.append(str(summary))

    prompt = get_re_ranking_prompt(query, doc_summaries)
    if LOG: print(f"Created re-ranking prompt")

    response = openai.ChatCompletion.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a veteran recruiter and also an expert in proof reading and validating the correctness of facts like location of company/university, skills and finding the perfert candidate for the requirements and rating them on the same."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10000,
        temperature=0.0,
        n=1,
        response_format={
            "type": "json_schema", 
            "json_schema": {
                "name": "ranking_response_schema",  # required string identifier
                "schema": ENHANCED_RE_RANK_SCHEMA
            }
        }
    )
    if LOG: print("Re-ranking response completed")
    reranked_docs = []
    try:
        ranking_str = response.choices[0].message['content'].strip()
        if LOG: print(f"ranking_str : {ranking_str}")
        ranking = json.loads(ranking_str)
        doc_list_sorted = sorted(ranking["results"], key=lambda obj: obj["ranking_score"], reverse = True)
        # print(f"doc_list_sorted : {doc_list_sorted}")
        for obj in doc_list_sorted:
            key = obj["_id"].strip()
            if key in docs_by_id and obj["ranking_score"] > 0: 
                cur_doc = docs_by_id[key]
                cur_doc["ranking_score"] = obj["ranking_score"]
                cur_doc["detailed_reason_for_ranking"] = obj["detailed_reason_for_ranking"]
                reranked_docs.append(cur_doc)
            else: 
                if LOG: print(f"key not found : {key}")
    except Exception as e:
        logging.error("Error occurred: %s", e, exc_info=True)
        # If parsing fails, fallback to original order
        ranking = list(range(len(docs_to_rerank)))
        if LOG: print("Failed to re-rank")
        reranked_docs = docs_to_rerank

    return reranked_docs


def fetch_mongo_docs(object_ids):
    # Convert to ObjectId type for MongoDB queries
    obj_id_objs = [ObjectId(oid) for oid in object_ids]
    docs = list(mongo_collection.find({"_id": {"$in": obj_id_objs}}))
    return docs

def eval_function(object_ids: list, template: str):
    url = "https://mercor-dev--search-eng-interview.modal.run/evaluate"

    if len(object_ids) > 10:
        object_ids = object_ids[:10]
    payload = json.dumps({
      "config_path": template,
      "object_ids": object_ids
    })
    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'yatharthlakhera75@gmail.com'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    eval_response = json.loads(response.text)
    print("\n================================= RESULT ============================================")
    print(f"{template} average_final_score -> {eval_response["average_final_score"]}")
    print("================================= RESULT ============================================")
    if LOG: print(f"\n Full Eval response for : {eval_response}")


# ==== MAIN PIPELINE ====

def main(search_obj: object):
    # Step 1: Rewrite search query using GPT
    hard_criteria = get_transformed_query(search_obj["query"], QUERY_REWRITE_PROMPT_HARD_CRITERIA)
    # soft_criteria = get_transformed_query(search_obj["query"], QUERY_REWRITE_PROMPT_SOFT_CRITERIA)
    rewritten_query = hard_criteria
    if LOG: print("[Step 1] Rewritten Query:", rewritten_query)

    # Step 2: Extract filter values
    filters = extract_filters(search_obj["query"])
    if LOG: print("[Step 2] Filter values extracted:", filters)

    # Step 3: Embed the query using Voyage-3
    embedding = create_embedding(search_obj["query"] + " " + rewritten_query)
    if LOG: print("[Step 3] Embedding created, first 5 dims:", embedding[:5])

    # Step 4: Qdrant vector search with filters and prestigeScore ordering
    matched_mongo_ids = query_qdrant(embedding, filters)
    if LOG: print("[Step 4] Qdrant returned MongoIDs:", matched_mongo_ids)

    # Step 5: Retrieve documents from MongoDB and print
    docs = fetch_mongo_docs(matched_mongo_ids)
    if LOG: print("[Step 5] Candidate documents:", len(docs))

    # Step 6 : Re-rank docs
    if (len(filters) > 0):
        country_name = filters['must'][0]['match']['value']
        rewritten_query = rewritten_query + "\n Note: Validate carefully if the eduction and experience is from country for scoring -> " + country_name
    reranked_docs = rerank_documents(rewritten_query, docs)

    # Batched reranking
    # final_rerank_docs = []
    # docs_batch = []
    # for doc in docs:
    #     docs_batch.append(doc)
    #     if (len(docs_batch) == 10):
    #         reranked_docs = rerank_documents(rewritten_query, docs_batch)
    #         final_rerank_docs.extend(reranked_docs)
    #         docs_batch = []
    # final_rerank_docs = sorted(final_rerank_docs, key=lambda obj: obj["ranking_score"], reverse = True)
    # # Final Reranking
    # reranked_docs = rerank_documents(rewritten_query, final_rerank_docs[:50])

    count = 0
    best_candidate_ids = []
    for doc in reranked_docs:
        doc_id = str(doc["_id"])
        if doc_id not in best_candidate_ids: best_candidate_ids.append(doc_id)
        count+=1
    print(f"best_candidate_ids : {best_candidate_ids}")

    # Step 7 : Eval
    if len(best_candidate_ids) > 0: 
        eval_function(best_candidate_ids, search_obj["template"])
    else:
        best_candidate_ids = [str(doc["_id"]) for doc in docs]
        print(f"Vector Only - best_candidate_ids : {best_candidate_ids}")
        eval_function(best_candidate_ids, search_obj["template"])


if __name__ == "__main__":
    # main(search_query["tax_lawyer"])
    # main(search_query["junior_corporate_lawyer"])
    # main(search_query["radiology"])
    # main(search_query["doctor_md"])
    # main(search_query["biology_expert"])
    # main(search_query["anthropology"])
    # main(search_query["mathematics_phd"])
    # main(search_query["quantitative_finance"])
    # main(search_query["bankers"])
    main(search_query["mechanical_engineers"])
