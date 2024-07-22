### Edges
def decide_to_generate(state):
    print("---ASSESS GRADED DOCUMENTS---")
    web_search = state["web_search"]

    if web_search == "yes":
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION---"
        )
        return "noGenerate"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"
    
def check_if_question(state):
    isQuestion = state["isQuestion"]
    if isQuestion == "yes":
        print("---USER ASKED QUESTION---")
        return "yes"
    else:
        print("---USER DID NOT ASK QUESTION---")
        return "no"