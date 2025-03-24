
from Agents.DocumentRagAgent.document_rag_agent import DocumentRagAgent


def main():
    
    # Interactive loop
    print("Ask me anything! (Type 'quit' to exit)")
    agent=DocumentRagAgent(path="C:\\Users\\YASH\\Desktop\\Hackathon\\knowledgegraph\\example\\Data\\Demo.pdf")
    while True:
        user_input = input("> ")
        if user_input.lower() == 'quit':
            break
        response = agent.run(user_input)
        print(response.get("output"))

if __name__ == "__main__":
    main()