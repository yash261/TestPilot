import asyncio
from Agents.CodeRagAgent.code_rag_agent import CodeRagAgent
from Agents.CodeRagAgent.service import InferenceService
from dotenv import load_dotenv
load_dotenv()

async def main():
    repo_dir="C:\\Users\\YASH\\Desktop\\Hackathon\\samplerepo"

    service=InferenceService()
    service.project_setup(repo_dir,True)
    await service.run_inference()

    knowledge_agent = CodeRagAgent()
    response = knowledge_agent.run("Explain main.java file and give me the code")
    print(response)

asyncio.run(main())