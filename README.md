
---

# Context-Aware Testing System for Financial Ecosystems

Welcome to the **Context-Aware Testing System**, a revolutionary approach to testing in the fast-evolving financial ecosystem. This project leverages Generative AI to dynamically generate and adapt test scenarios, focusing on end-to-end functional testing for financial systems. Developed by Chirag Garg, Dhruv Kumar, Mohitpal Singh, and Yash Goel.

## Table of Contents
- [Introduction](#introduction)
- [Problem Statement](#problem-statement)
- [Our Solution](#our-solution)
- [Key Benefits](#key-benefits)
- [Technical Architecture](#technical-architecture)
- [Workflow](#workflow)
- [Future Enhancements](#future-enhancements)
- [Conclusion](#conclusion)

---

## Introduction
In the complex world of financial ecosystems, robust testing is both critical and challenging. Our context-aware testing system redefines this process by:
- Understanding the codebase dynamically.
- Leveraging existing test cases.
- Adding new test cases as the code evolves.

While supporting API and unit testing, our primary focus is on **end-to-end functional testing**, ensuring comprehensive validation tailored to financial systems.

---

## Problem Statement
Financial ecosystems feature interconnected systems and APIs, yet traditional testing relies on static mock tools, leading to:
- Inefficiencies.
- High costs.
- Limited adaptability.

**Challenge**: Build a context-aware testing system using Generative AI to dynamically generate and adapt test scenarios, reducing manual effort while improving coverage and effectiveness.

---

## Our Solution
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

---

## Key Benefits
- **Enhanced Test Coverage**: Comprehensive validation of financial systems.
- **Reduced Manual Effort**: Automation minimizes human intervention.
- **Improved Accuracy**: Context-aware scenarios reduce errors.
- **Cost Efficiency**: Lower testing overhead.
- **Scalable & Adaptive**: Grows with your system.
- **Risk Mitigation**: Ensures reliability in complex ecosystems.

---

## Technical Architecture
Our architecture integrates multiple components for seamless operation:

- **Knowledge Graph**: Stores codebase relationships.
- **Vector Embeddings**: Captures document context.
- **LLM Agents**: Drive context fetching, BDD generation, and script creation.
- **Playwright**: Executes end-to-end tests.
- **Graph DB & Vector DB**: Enable scalable data management.

![Knowledge Graph & Vector Embeddings Generation](https://github.com/yash261/KnowledgeGraphForCode/blob/main/Images/Knowledge_Graph_and_Embeddings.png)

---

## Workflow
1. Fetch context from code and documents.
2. Generate BDD scenarios.
3. Create Playwright test scripts.
4. Execute tests and validate results.
5. Update storage for future adaptability.

![Architectural Workflow](https://github.com/yash261/KnowledgeGraphForCode/blob/main/Images/Workflow_Diagram.png)

---

## Future Enhancements
We’re planning exciting upgrades:
- **Kafka**: Parallel testing of multiple BDD scenarios via a Kafka Queue.
- **GitHub Actions**: Auto-detect new code and generate test cases.
- **Grafana**: Integrate with monitoring tools for test reports and coverage.
- **CI/CD Integration**: Convert test cases into config files for automated execution.
- **JIRA Integration**: Fetch context from JIRA for new test cases.

---

## Conclusion
Our context-aware testing system, powered by Generative AI, transforms financial system validation by:
- Dynamically generating and adapting test scenarios.
- Minimizing manual effort.
- Enhancing coverage and reliability.

This scalable, cost-efficient solution reduces risks and paves the way for resilient financial ecosystems. Let’s build the future of testing together!

---

### How to Use
1. Clone this repository:  
   ```bash
   git clone https://github.com/yash261/KnowledgeGraphForCode/tree/main
   ```
2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```
3. Setup Pinecone and Neo4j instances and place in .env file

4. Run Command:
    ```bash
   python main.py
   ```
   
---

### Contributors
- Chirag Garg
- Dhruv Kumar
- Mohitpal Singh
- Yash Goel

---
