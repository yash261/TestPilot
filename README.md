
---

# 🖥️ Context-Aware Testing System for Financial Ecosystems

Welcome to the **Context-Aware Testing System**, a revolutionary approach to testing in the fast-evolving financial ecosystem. This project leverages Generative AI to dynamically generate and adapt test scenarios, focusing on end-to-end functional testing for financial systems. 

## Table of Contents
- [Introduction](#introduction)
- [Inspiration](#Inspiration)
- [What it Does](#What-it-Does)
- [How We Built it](#How-We-Built-it)
- [Challenges We Faced](#Challenges-We-Faced)
- [How to Run](#How-to-Run)
- [Tech Stack](#Tech-Stack)
- [Team](#Team)


## 🧐 Introduction
In the complex world of financial ecosystems, robust testing is both critical and challenging. Our context-aware testing system redefines this process by:
- Understanding the codebase dynamically.
- Leveraging existing test cases.
- Adding new test cases as the code evolves.

While supporting API and unit testing, our primary focus is on **end-to-end functional testing**, ensuring comprehensive validation tailored to financial systems.




## 💡 Inspiration
Financial ecosystems feature interconnected systems and APIs, yet traditional testing relies on static mock tools, leading to:
- Inefficiencies.
- High costs.
- Limited adaptability.

**Challenge**: Build a context-aware testing system using Generative AI to dynamically generate and adapt test scenarios, reducing manual effort while improving coverage and effectiveness.


## ⚙️ What it Does
Our system integrates advanced AI and automation to streamline testing:

1. **Dynamic Context Fetching**  
   - An LLM Agent retrieves project code context from a Knowledge Graph.
   - Another LLM Agent extracts context from project documents using Vector Embeddings.

2. **Intelligent BDD Generation**  
   - Generates Behavior-Driven Development (BDD) scenarios tailored to the financial ecosystem's codebase.

3. **Automated Script Creation**  
   - Transforms BDD scenarios into executable Playwright test scripts.

4. **End-to-End Testing with Playwright**  
   - Executes test scripts, focusing on functional testing, with feedback for continuous improvement.

5. **Adaptive Test Management**  
   - Validates results, saves successful tests, and updates the Graph DB for future context awareness.

6. **Scalable Data Integration**  
   - Uses Graph DB and Vector DB for efficient storage and retrieval of code, context, and test data.

Our context-aware testing system, powered by Generative AI, transforms financial system validation by:
- Dynamically generating and adapting test scenarios.
- Minimizing manual effort.
- Enhancing coverage and reliability.

### Key Benefits
- **Enhanced Test Coverage**: Comprehensive validation of financial systems.
- **Reduced Manual Effort**: Automation minimizes human intervention.
- **Improved Accuracy**: Context-aware scenarios reduce errors.
- **Cost Efficiency**: Lower testing overhead.
- **Scalable & Adaptive**: Grows with your system.
- **Risk Mitigation**: Ensures reliability in complex ecosystems.


## 🛠️ How We Built it
Our architecture integrates multiple components for seamless operation:

- **Knowledge Graph**: Stores codebase relationships.
- **Vector Embeddings**: Captures document context.
- **LLM Agents**: Drive context fetching, BDD generation, and script creation.
- **Playwright**: Executes end-to-end tests.
- **Graph DB & Vector DB**: Enable scalable data management.

![Knowledge Graph & Vector Embeddings Generation](https://github.com/yash261/KnowledgeGraphForCode/blob/main/Images/Knowledge_Graph_and_Embeddings.png)


### 👷 Workflow
1. Fetch context from code and documents.
2. Generate BDD scenarios.
3. Create Playwright test scripts.
4. Execute tests and validate results.
5. Update storage for future adaptability.

![Architectural Workflow](https://github.com/yash261/KnowledgeGraphForCode/blob/main/Images/Workflow_Diagram.png)


### ✨ Future Enhancements
We’re planning exciting upgrades:
- **GitHub Actions**: Auto-detect new code and generate test cases.
- **Grafana**: Integrate with monitoring tools for test reports and coverage.
- **CI/CD Integration**: Convert test cases into config files for automated execution.
- **JIRA Integration**: Fetch context from JIRA for new test cases.


### 🏃 How to Run
1. Clone this repository:  
   ```bash
   git clone https://github.com/ewfx/catfe-g-e-n-zai.git
   ```

2) Navigate to code directory:
   ```bash
   cd code/scripts
   ```

3. Create a virtual environment:  
   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:  
   - On Windows:  
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:  
     ```bash
     source venv/bin/activate
     ```

5. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

6. Setup Pinecone and Neo4j instances and create a `.env` file in the root directory with the following format:  
   ```env
   GOOGLE_API_KEY="your_google_api_key"
   neo4j_uri="your_neo4j_uri"
   neo4j_username="your_neo4j_username"
   neo4j_password="your_neo4j_password"
   PINECONE_API_KEY="your_pinecone_api_key"
   PINECONE_ENV="your_pinecone_environment"
   INDEX_NAME="your_index_name"
   ```

7. Install node dependencies:  
   ```bash
   npm install
   ```

8. To run the test executor service:  
   ```bash
   python test_executor.py
   ```

9. Run the bdd generator service:  
   ```bash
   streamlit run ui.py
   ```

10. To run the complete generated test suite
      ```bash
      python runTestSuite.py
      ```
   

## 📚 Tech Stack
1. Frontend: Streamlit
2. Backend: Flask
3. Database: Pinecone, Neo4j
4. LLM: Google Gemini
5. Framework: LangChain, LangGraph, Tree Sitter
6. Language Used: Python, Javascript

---

