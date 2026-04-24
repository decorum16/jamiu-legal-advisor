from app.services.legal.answer_pipeline import LegalAnswerPipeline
from app.services.legal.case_retrieval import CaseRetriever
from app.services.legal.legal_answer import ConstitutionRetriever, StatuteRetriever
from app.services.llm.ai_service import AIService


def get_legal_answer_pipeline() -> LegalAnswerPipeline:
    statute_retriever = StatuteRetriever()
    constitution_retriever = ConstitutionRetriever()
    case_retriever = CaseRetriever()
    llm_client = AIService()

    return LegalAnswerPipeline(
        statute_retriever=statute_retriever,
        constitution_retriever=constitution_retriever,
        case_retriever=case_retriever,
        llm_client=llm_client,
    )