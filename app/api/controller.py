from app.services.processor import AIChiefOfStaffProcessor
from app.api.schema import ProcessRequest, ProcessResponse
import uuid

processor = None

def init_process(llm, tools, db):
    global processor
    processor = AIChiefOfStaffProcessor(llm, tools, db)

def process_handler(request):
    global processor

    result = processor.process_input(request.text)

    return ProcessResponse(
        run_id = result.metadata.run_id if result.metadata.run_id else str(uuid.uuid4()),
        tasks=result.tasks,
        decisions=result.decisions,
        risks=result.risks,
        summary=result.summary
    )