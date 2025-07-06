import re
import spacy
from sentence_transformers import SentenceTransformer, util

nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer("all-MiniLM-L6-v2")

def parse_query(text):
    doc = nlp(text)
    result = {"year": None, "sem": None, "subject": None, "course": None}

    for ent in doc.ents:
        if ent.label_ == "DATE" and ent.text.isdigit():
            result["year"] = int(ent.text)

    for i, token in enumerate(doc):
        if token.text.lower() in {"sem", "semester"}:
            if i + 1 < len(doc) and doc[i + 1].like_num:
                result["sem"] = int(doc[i + 1].text)

    subjects = [
        "Bengali", "Botany", "Chemistry", "Commerce", "Computer Science", "Economics",
        "Education", "Electronics", "English", "ENVS", "Film Studies", "History",
        "Journalism", "Mathematics", "Philosophy", "Physics", "Pol Science", "Zoology"
    ]
    for s in subjects:
        if s.lower() in text.lower():
            result["subject"] = s

    if "hons" in text.lower():
        result["course"] = "Hons"
    elif "gen" in text.lower():
        result["course"] = "Gen"

    return result

def semantic_ranking(query_text, metadata, top_k=10, threshold=0.3):
    q_emb = model.encode(query_text, convert_to_tensor=True)
    doc_texts = [
        " ".join([m["subject"], m["course"], m["semester_folder"], m["name"]])
        for m in metadata
    ]
    doc_emb = model.encode(doc_texts, convert_to_tensor=True)
    scores = util.cos_sim(q_emb, doc_emb).cpu().numpy()[0]

    ranked = []
    for i, score in enumerate(scores):
        if score >= threshold:
            ranked.append((metadata[i], score))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in ranked[:top_k]]
