from app.agents.decision_agent import create_decision_agent
from app.agents.execution_agent import create_execution_agent
from app.agents.intake_agent import create_intake_agent
from app.agents.task_agent import create_task_agent
from app.agents.summary_agent import create_summary_agent   
from app.agents.risk_agent import create_risk_agent
from app.schemas.output_schema import Task, Decision, Risk, OutputSchema, AgentMetadata
import json, uuid
from datetime import datetime

class AIChiefOfStaffProcessor:
    def __init__(self, llm, tools, db):
        self.llm = llm
        self.tools = tools
        self.db = db
        self.intake_agent = create_intake_agent(llm)
        self.task_agent = create_task_agent(llm)
        self.decision_agent = create_decision_agent(llm)
        self.risk_agent = create_risk_agent(llm)
        self.execution_agent = create_execution_agent(llm, tools)
        self.summary_agent = create_summary_agent(llm)


    def process_input(self, text):
        # Step 1: Intake and preprocess input
        preprocessed_input = self.intake_agent.run(text)

        # Step 2: Extract tasks, decisions, and risks
        tasks_raw = self.task_agent.run(preprocessed_input)
        decisions_raw = self.decision_agent.run(preprocessed_input)
        risks_raw = self.risk_agent.run(preprocessed_input)

        # Parse raw JSON outputs into structured data
        tasks = [Task(**task) for task in json.loads(tasks_raw)]
        decisions = [Decision(**decision) for decision in json.loads(decisions_raw)]
        risks = [Risk(**risk) for risk in json.loads(risks_raw)]

        # Step 3: Execute operations based on extracted data
        # execution_status = self.execution_agent.run({
        #     "tasks": tasks,
        #     "decisions": decisions,
        #     "risks": risks
        # })

        # Step 4: Generate summary of the process
        # summary = self.summary_agent.run({
        #     "tasks": tasks,
        #     "decisions": decisions,
        #     "risks": risks,
        #     "execution_status": execution_status
        # })

        output = {
            "tasks": tasks,
            "decisions": decisions,
            "risks": risks,
            # "execution_status": execution_status,
            # "summary": summary
        }

        for _ in range(2):
            reviewed = self.critic_agent.run(json.dumps(output, default=str))
            output = json.loads(reviewed)

            try:
                validated_tasks = [Task(**task) for task in output.get("tasks", [])]
                validated_decisions = [Decision(**decision) for decision in output.get("decisions", [])]
                validated_risks = [Risk(**risk) for risk in output.get("risks", [])]
                
                output = {
                    "tasks": validated_tasks,
                    "decisions": validated_decisions,
                    "risks": validated_risks,
                }
            except Exception as e:
                # Handle validation error
                print(f"Validation error: {e}")
                # Optionally return raw output or raise
                raise


            self.execution_agent.run({
                "tasks": output["tasks"],
                "decisions": output["decisions"],
                "risks": output["risks"]
            })

            self.db.save_tasks(t.dict() for t in output["tasks"])

            summary = self.summary_agent.run({
                "tasks": output["tasks"],
                "decisions": output["decisions"],
                "risks": output["risks"],
            })

        final_output = OutputSchema(
            tasks=output["tasks"],
            decisions=output["decisions"],
            risks=output["risks"],
            summary=summary,
            metadata=AgentMetadata(
                source="cli",
                processed_at=datetime.now(datetime.timezone.utc),
                run_id=str(uuid.uuid4())
            )
        )
        return final_output
            