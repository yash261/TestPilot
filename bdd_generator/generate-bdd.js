// test-generator/generate-tests.js
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const fs = require('fs').promises;
const path = require('path');
const { parse } = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const { GoogleGenerativeAI } = require('@google/generative-ai');
const { pipeline } = require('@xenova/transformers');
const dotenv = require('dotenv');
import { fileURLToPath } from 'url';
const pdfParse = require('pdf-parse');
const minimist = require('minimist');

// Load environment variables from .env file
const envConfig = dotenv.config();
if (envConfig.error) {
  throw new Error('Failed to load .env file: ' + envConfig.error.message);
}

if (!process.env.GOOGLE_API_KEY) {
  throw new Error('GOOGLE_API_KEY is not defined in .env file');
}

// Parse command-line arguments
// Parse command-line arguments

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const args = minimist(process.argv.slice(2));
const COMPONENTS_DIR = args.components ? path.resolve(args.components) : path.resolve(__dirname, '../frontend/src/components');
const DESIGN_PDF_PATH = args.design ? path.resolve(args.design) : null; // Allow null if not provided
const CACHE_FILE = path.resolve(__dirname, './cache.json');
const FEATURES_DIR = path.resolve(__dirname, '../tests/features');
const MEMORY_FILE = path.resolve(__dirname, './memory-history.json');
const additional_info = args['additional_info'] ? args['additional_info'] : 'Use previous history and context for generating tests and getting test info'; // Custom default

// Parse test credentials (e.g., --test-credentials "user,pass")
// const [TEST_USER, TEST_PASSWORD] = (args['test-credentials'] || 'user,pass').split(',').map(s => s.trim());

// Validate provided paths (only if design PDF is provided)
async function validatePaths() {
  try {
    await fs.access(COMPONENTS_DIR);
    if (DESIGN_PDF_PATH) {
      await fs.access(DESIGN_PDF_PATH);
    } else {
      console.log('No design PDF provided; will attempt to use cached design knowledge graph');
    }
  } catch (error) {
    console.error('Error: Invalid path provided.');
    console.error(`Components directory: ${COMPONENTS_DIR}`);
    if (DESIGN_PDF_PATH) console.error(`Design PDF: ${DESIGN_PDF_PATH}`);
    console.error('Usage: node generate-tests.js --components <path> [--design <pdf-path>] --additional_info "changes"');
    process.exit(1);
  }
}

// Initialize Gemini API with gemini-2.0-flash
const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

// Initialize embedding model
let embedder;
async function initializeModels() {
  if (!embedder) {
    console.log('Initializing embedder...');
    embedder = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    console.log('Embedder initialized');
  }
  return { embedder };
}

// Generate embedding for code or text
async function generateEmbedding(text) {
  const { embedder } = await initializeModels();
  const result = await embedder(text, { pooling: 'mean', normalize: true });
  return Array.from(result.data);
}

// Cosine similarity function
function cosineSimilarity(vecA, vecB) {
  if (!vecA || !vecB || vecA.length !== vecB.length) {
    console.warn('Invalid vectors for cosine similarity:', vecA, vecB);
    return 0;
  }
  const dotProduct = vecA.reduce((sum, a, i) => sum + a * vecB[i], 0);
  const magA = Math.sqrt(vecA.reduce((sum, a) => sum + a * a, 0));
  const magB = Math.sqrt(vecB.reduce((sum, b) => sum + b * b, 0));
  return magB === 0 || magA === 0 ? 0 : dotProduct / (magA * magB);
}

// Load or initialize cache
async function loadCache() {
  try {
    const data = await fs.readFile(CACHE_FILE, 'utf-8');
    const cache = JSON.parse(data);
    if (!cache.files) cache.files = {};
    if (!cache.knowledgeGraph) cache.knowledgeGraph = { design: {}, code: {} };
    if (!cache.tests) cache.tests = {};
    return cache;
  } catch (error) {
    console.log('Cache not found or invalid, initializing new cache:', error.message);
    return { files: {}, knowledgeGraph: { design: {}, code: {} }, tests: {} };
  }
}

async function saveCache(cache) {
  await fs.writeFile(CACHE_FILE, JSON.stringify(cache, null, 2));
}

// Load memory history from JSON file
async function loadMemoryHistory() {
  try {
    const data = await fs.readFile(MEMORY_FILE, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    console.log('No prior memory history found, starting fresh.');
    return {};
  }
}

// Save memory history to JSON file
async function saveMemoryHistory(history) {
  await fs.writeFile(MEMORY_FILE, JSON.stringify(history, null, 2));
}

// Extract docstring from component code
async function extractDocstring(code, componentName) {
  const ast = parse(code, { sourceType: 'module', plugins: ['jsx', 'typescript'] });
  let docstring = '';
  traverse(ast, {
    FunctionDeclaration(path) {
      if (path.node.id.name === componentName && path.node.leadingComments) {
        const comment = path.node.leadingComments.find(c => c.type === 'CommentBlock' || c.type === 'CommentLine');
        if (comment) docstring = comment.value.replace(/\*/g, '').trim();
      }
    },
    VariableDeclaration(path) {
      if (path.node.declarations[0]?.id.name === componentName && path.node.leadingComments) {
        const comment = path.node.leadingComments.find(c => c.type === 'CommentBlock' || c.type === 'CommentLine');
        if (comment) docstring = comment.value.replace(/\*/g, '').trim();
      }
    },
  });
  return docstring || 'No docstring provided.';
}

// Extract React component code
async function extractComponentCode(code, componentName) {
  const ast = parse(code, { sourceType: 'module', plugins: ['jsx', 'typescript'] });
  let componentCode = code;
  for (const node of ast.program.body) {
    if (
      (node.type === 'FunctionDeclaration' && node.id.name === componentName) ||
      (node.type === 'VariableDeclaration' &&
        node.declarations[0]?.id.name === componentName &&
        (node.declarations[0].init.type === 'ArrowFunctionExpression' || node.declarations[0].init.type === 'FunctionExpression'))
    ) {
      componentCode = code.slice(node.start, node.end);
      break;
    } else if (node.type === 'ExportDefaultDeclaration' && node.declaration.name === componentName) {
      componentCode = code.slice(node.start, node.end);
      break;
    }
  }
  return componentCode;
}

// Retrieve similar context using in-memory cache
async function retrieveSimilarContext(currentCode, cache, filePath) {
  const currentEmbedding = await generateEmbedding(currentCode);
  let bestMatch = null;
  let highestSimilarity = -1;

  for (const [cachedPath, entry] of Object.entries(cache.files)) {
    if (entry.embedding) {
      const similarity = cosineSimilarity(currentEmbedding, entry.embedding);
      if (similarity > highestSimilarity) {
        highestSimilarity = similarity;
        bestMatch = { filePath: cachedPath, code: entry.code, tests: cache.tests[cachedPath], similarity };
      }
    }
  }

  if (highestSimilarity > 0.8) {
    console.log(`Retrieved similar context from ${bestMatch.filePath} with similarity ${highestSimilarity}`);
    return bestMatch;
  }
  console.log('No sufficiently similar context found for', filePath);
  return null;
}

// Clean markdown fences from test code
function cleanTestCode(testCode) {
  let cleaned = testCode.trim();
  cleaned = cleaned.replace(/^```(?:gherkin)?\s*\n?/i, '');
  cleaned = cleaned.replace(/\n?```\s*$/, '');
  cleaned = cleaned.replace(/```/g, '');
  return cleaned.trim();
}

// Split Gherkin text into separate feature files
function splitGherkinIntoFeatures(gherkinText, componentName) {
  const lines = gherkinText.split('\n');
  const features = [];
  let currentFeature = { header: [], scenarios: [] };
  let currentScenario = null;

  for (const line of lines) {
    const trimmedLine = line.trim();
    if (trimmedLine.startsWith('Feature:')) {
      if (currentFeature.scenarios.length > 0) {
        features.push(currentFeature);
        currentFeature = { header: [], scenarios: [] };
      }
      currentFeature.header.push(line);
    } else if (trimmedLine.startsWith('Scenario:')) {
      if (currentScenario) {
        currentFeature.scenarios.push(currentScenario);
      }
      currentScenario = [line];
    } else if (currentScenario) {
      currentScenario.push(line);
    } else {
      currentFeature.header.push(line);
    }
  }
  if (currentScenario) {
    currentFeature.scenarios.push(currentScenario);
  }
  if (currentFeature.header.length > 0 || currentFeature.scenarios.length > 0) {
    features.push(currentFeature);
  }

  const featureFiles = [];
  features.forEach(feature => {
    feature.scenarios.forEach((scenario, index) => {
      const scenarioName = scenario[0].trim().replace('Scenario:', '').trim().toLowerCase().replace(/\s+/g, '-');
      const fileName = `${componentName.toLowerCase()}-${scenarioName}.feature`;
      const content = [...feature.header, '', ...scenario].join('\n');
      featureFiles.push({ fileName, content });
    });
  });

  return featureFiles;
}

// Chunk PDF text into sections
function chunkPdfText(text) {
  const chunks = [];
  const lines = text.split('\n');
  let currentChunk = [];
  for (const line of lines) {
    if (line.match(/^\d+\.\s/) || line.match(/^\d+\.\d+\s/)) {
      if (currentChunk.length > 0) {
        chunks.push(currentChunk.join(' '));
        currentChunk = [];
      }
    }
    currentChunk.push(line.trim());
  }
  if (currentChunk.length > 0) {
    chunks.push(currentChunk.join(' '));
  }
  return chunks;
}

// Extract entities and relationships from PDF chunks
async function extractEntitiesAndRelations(chunk) {
  const entities = { components: [], routes: [], apis: [], actions: [], credentials: null, baseUrl: null };
  const relations = [];

  const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1);

  const queries = {
    landingPage: "is the first page",
    navigation: "navigates-to",
    requiresLogin: "requires login",
    route: "at ",
    api: "API:",
  };

  const chunkEmbedding = await generateEmbedding(chunk);

  const componentRegex = /([A-Z][a-zA-Z]+)\s+Page/gi;
  let match;
  while ((match = componentRegex.exec(chunk)) !== null) {
    const componentName = match[1];
    if (!entities.components.includes(componentName) && componentName !== "first" && componentName !== "other") {
      entities.components.push(componentName);
    }
  }

  for (const component of entities.components) {
    const componentContext = chunk.toLowerCase().includes(component.toLowerCase()) ? chunk : '';

    if (componentContext) {
      const landingEmbedding = await generateEmbedding(queries.landingPage);
      if (cosineSimilarity(chunkEmbedding, landingEmbedding) > 0.6) {
        console.log(`Detected ${component} as landing page in chunk: ${chunk}`);
      }

      const navEmbedding = await generateEmbedding(queries.navigation);
      if (cosineSimilarity(chunkEmbedding, navEmbedding) > 0.6) {
        const navMatches = [...chunk.matchAll(/navigates-to\s+([A-Za-z]+)\s+with\s+button\s+data-testid="([^"]+)"/gi)];
        for (const navMatch of navMatches) {
          const targetComponent = capitalize(navMatch[1]);
          const navigationId = navMatch[2];
          if (!entities.components.includes(targetComponent)) {
            entities.components.push(targetComponent);
          }
          relations.push({ from: component, to: targetComponent, relation: 'navigates-to', navigationId });
          console.log(`Detected navigation: ${component} -> ${targetComponent} with ${navigationId}`);
        }
      }

      const reqEmbedding = await generateEmbedding(queries.requiresLogin);
      if (cosineSimilarity(chunkEmbedding, reqEmbedding) > 0.6 || chunk.match(/Requires:\s*Login/i)) {
        relations.push({ from: component, to: 'Login', relation: 'requires' });
      }

      const routeMatch = chunk.match(/Route:\s*[A-Za-z]+\s+at\s+([\/][a-z\/]*)/i);
      if (routeMatch) {
        entities.routes.push(routeMatch[1]);
        relations.push({ from: component, to: routeMatch[1], relation: 'at-route' });
      }

      const apiEmbedding = await generateEmbedding(queries.api);
      if (cosineSimilarity(chunkEmbedding, apiEmbedding) > 0.6) {
        const apiMatch = chunk.match(/(GET|POST|PUT|DELETE)?\s*\/api\/[a-z\/<>-]+/i);
        if (apiMatch) {
          const apiPath = apiMatch[0].trim();
          entities.apis.push(apiPath);
          relations.push({ from: component, to: apiPath, relation: 'uses' });
        }
      }
    }
  }

  const credentialsMatch = chunk.match(/username "([^"]+)" and password "([^"]+)"/);
  if (credentialsMatch && entities.components.length > 0) {
    entities.credentials = { username: credentialsMatch[1], password: credentialsMatch[2] };
  }

  const baseUrlMatch = chunk.match(/Base URL: (http:\/\/localhost:[0-9]+)/i);
  if (baseUrlMatch) entities.baseUrl = baseUrlMatch[1];

  return { entities, relations };
}

// Build design knowledge graph from PDF
async function buildDesignKnowledgeGraph(pdfPath, cache) {
  const pdfBuffer = await fs.readFile(pdfPath);
  const fullText = (await pdfParse(pdfBuffer)).text;
  const pdfHash = require('crypto').createHash('md5').update(fullText).digest('hex');
  if (cache.knowledgeGraph.design[pdfPath] && cache.knowledgeGraph.design[pdfPath].hash === pdfHash) {
    console.log('Using cached design knowledge graph');
    return cache.knowledgeGraph.design[pdfPath].graph;
  }

  console.log('Building design knowledge graph with semantic search...');
  const chunks = chunkPdfText(fullText);
  const graph = { nodes: {}, edges: [], baseUrl: null };

  for (const chunk of chunks) {
    // console.log('Processing chunk:', chunk);
    const { entities, relations } = await extractEntitiesAndRelations(chunk);

    for (const component of entities.components) {
      graph.nodes[component] = graph.nodes[component] || { type: 'component' };
      if (entities.credentials && cosineSimilarity(await generateEmbedding(chunk), await generateEmbedding("is the first page")) > 0.6) {
        graph.nodes[component].credentials = entities.credentials;
        graph.nodes[component].isLandingPage = true;
      }
    }

    entities.routes.forEach(route => {
      graph.nodes[route] = { type: 'route' };
    });

    entities.apis.forEach(api => {
      const method = api.match(/(GET|POST|PUT|DELETE)/i)?.[0] || 'GET';
      graph.nodes[api] = { type: 'api', method };
    });

    entities.actions.forEach(action => {
      graph.nodes[action] = { type: 'action' };
    });

    if (entities.baseUrl && !graph.baseUrl) {
      graph.baseUrl = entities.baseUrl;
    }

    relations.forEach(rel => {
      if (rel.relation === 'at-route') {
        graph.nodes[rel.from].route = rel.to;
      } else if (rel.relation === 'requires') {
        graph.nodes[rel.from].requiresLogin = true;
      }
      graph.edges.push(rel);
    });
  }

  const landingQueryEmbedding = await generateEmbedding("is the first page");
  let landingPageSet = false;
  for (const node of Object.keys(graph.nodes)) {
    if (graph.nodes[node].type === 'component') {
      const nodeContext = fullText.toLowerCase().includes(node.toLowerCase()) ? fullText : '';
      if (nodeContext && (cosineSimilarity(await generateEmbedding(nodeContext), landingQueryEmbedding) > 0.6 || nodeContext.includes(`${node.toLowerCase()} at /`))) {
        graph.nodes[node].isLandingPage = true;
        landingPageSet = true;
        console.log(`Identified ${node} as landing page via semantic search or route /`);
      }
    }
  }

  if (!landingPageSet && graph.nodes['Login']) {
    graph.nodes['Login'].isLandingPage = true;
    console.log('No landing page detected; defaulting to Login');
  }

  // console.log('Graph nodes:', JSON.stringify(graph.nodes, null, 2));
  // console.log('Graph edges:', JSON.stringify(graph.edges, null, 2));
  console.log('Base URL:', graph.baseUrl);

  cache.knowledgeGraph.design[pdfPath] = { hash: pdfHash, graph };
  await saveCache(cache);
  return graph;
}

// Build enhanced code knowledge graph from component code
async function buildCodeKnowledgeGraph(filePath, code, componentName, cache) {
  const codeHash = require('crypto').createHash('md5').update(code).digest('hex');
  if (cache.knowledgeGraph.code[filePath] && cache.knowledgeGraph.code[filePath].hash === codeHash) {
    console.log(`Using cached code knowledge graph for ${filePath}`);
    return cache.knowledgeGraph.code[filePath].graph;
  }

  console.log(`Building code knowledge graph for ${componentName}`);
  const graph = { nodes: {}, edges: [], baseUrl: null };

  const ast = parse(code, { sourceType: 'module', plugins: ['jsx', 'typescript'] });
  graph.nodes[componentName] = { type: 'component' };

  traverse(ast, {
    JSXElement(path) {
      const elementName = path.node.openingElement.name.name.toLowerCase();
      if (['button', 'input', 'form'].includes(elementName)) {
        const text = path.node.children.find(child => child.type === 'JSXText')?.value?.trim();
        const id = path.node.openingElement.attributes.find(attr => attr.name.name === 'id')?.value?.value;
        const onClick = path.node.openingElement.attributes.find(attr => attr.name.name === 'onClick');
        const key = text || id || `${elementName}-${path.node.start}`;
        graph.nodes[key] = { type: 'element', tag: elementName, text };
        graph.edges.push({ from: componentName, to: key, relation: 'contains' });
        if (onClick) graph.nodes[key].hasAction = true;
      }
    },
    CallExpression(path) {
      if (path.node.callee.name === 'navigate' || (path.node.callee.property && path.node.callee.property.name === 'push')) {
        const route = path.node.arguments[0]?.value;
        if (route) {
          graph.nodes[route] = { type: 'route' };
          graph.edges.push({ from: componentName, to: route, relation: 'navigates-to' });
        }
      }
    },
  });

  // console.log(`Code graph for ${componentName}:`, JSON.stringify(graph, null, 2));
  cache.knowledgeGraph.code[filePath] = { hash: codeHash, graph };
  await saveCache(cache);
  return graph;
}

// Merge design and code knowledge graphs
function mergeKnowledgeGraphs(designGraph, codeGraph, componentName) {
  const mergedGraph = {
    nodes: { ...designGraph.nodes, ...codeGraph.nodes },
    edges: [...designGraph.edges, ...codeGraph.edges],
    baseUrl: designGraph.baseUrl || codeGraph.baseUrl,
  };

  for (const node in codeGraph.nodes) {
    if (designGraph.nodes[node]) {
      mergedGraph.nodes[node] = { ...designGraph.nodes[node], ...codeGraph.nodes[node] };
    }
  }

  if (mergedGraph.nodes[componentName]) {
    mergedGraph.nodes[componentName] = {
      ...mergedGraph.nodes[componentName],
      ...codeGraph.nodes[componentName],
    };
  }

//   console.log(`Merged graph for ${componentName}:`, JSON.stringify(mergedGraph, null, 2));
  return mergedGraph;
}

// Get component-specific context from merged graph
function getComponentContext(mergedGraph, componentName) {
  const context = [];
  const node = mergedGraph.nodes[componentName] || {};

  if (node.type === 'component') {
    context.push(`Component: ${componentName}`);
    if (node.isLandingPage) context.push('Is Landing Page: true');
    if (node.route) context.push(`Route: ${node.route}`);
    if (node.requiresLogin) context.push('Requires Login: true');
    if (node.credentials) context.push(`Credentials: ${JSON.stringify(node.credentials)}`);
  }

  mergedGraph.edges.forEach(edge => {
    if (edge.from === componentName) {
      if (edge.relation === 'navigates-to') {
        context.push(`Navigates to: ${edge.to} with navigationId: ${edge.navigationId || 'N/A'}`);
      } else if (edge.relation === 'uses') {
        context.push(`Uses API: ${edge.to}`);
      } else if (edge.relation === 'contains') {
        const el = mergedGraph.nodes[edge.to];
        context.push(`Contains Element: ${edge.to} (${el.tag}${el.hasAction ? ', actionable' : ''})`);
      }
    }
  });

  context.push(`Base URL: ${mergedGraph.baseUrl || 'Not specified'}`);
  return context.join('\n');
}

// Determine test order based on design graph
function determineTestOrder(componentFiles, designGraph) {
  const orderedFiles = [];
  const remainingFiles = [...componentFiles];

  for (const node in designGraph.nodes) {
    if (designGraph.nodes[node].type === 'component' && designGraph.nodes[node].isLandingPage) {
      const fileName = `${node}.js`;
      const index = remainingFiles.indexOf(fileName);
      if (index !== -1) {
        orderedFiles.push(fileName);
        remainingFiles.splice(index, 1);
        break;
      }
    }
  }

  while (remainingFiles.length > 0) {
    let added = false;
    for (const edge of designGraph.edges) {
      if (edge.relation === 'navigates-to' && orderedFiles.includes(`${edge.from}.js`)) {
        const targetFile = `${edge.to}.js`;
        const index = remainingFiles.indexOf(targetFile);
        if (index !== -1) {
          orderedFiles.push(targetFile);
          remainingFiles.splice(index, 1);
          added = true;
          break;
        }
      }
    }
    if (!added) {
      orderedFiles.push(remainingFiles.shift());
    }
  }

  return orderedFiles;
}

async function generateComponentTest(codeSnippet, componentContext, componentName, similarContext, baseUrl, docstring) {
  const contextSection = similarContext 
    ? `
      **Similar Previous BDD Scenarios:**
      Code:
      \`\`\`javascript
      ${similarContext.code}
      \`\`\`
      Scenarios:
      \`\`\`gherkin
      ${similarContext.tests}
      \`\`\`
      Similarity: ${similarContext.similarity}
    `
    : 'No similar previous code or scenarios found.';

  const memoryHistoryStore = await loadMemoryHistory();
  const memoryHistory = memoryHistoryStore[componentName] || [];
  console.log(`Loaded memory history for ${componentName}:`, JSON.stringify(memoryHistory, null, 2));

  const memoryString = memoryHistory.length > 0 
    ? `**Conversation History (Memory Buffer):**\n${memoryHistory.map(entry => 
        `${entry.role}: ${entry.content}`).join('\n')}`
    : 'No prior conversation history available for this component.';

  const useFullCode = !docstring || docstring.length < 20 || codeSnippet.length < 1000;
  const codeSection = useFullCode 
    ? `**React Component Code:**
      \`\`\`javascript
      ${codeSnippet.length > 1000 ? codeSnippet.slice(0, 1000) + '...' : codeSnippet}
      \`\`\``
    : '**Note:** Full code omitted due to length or sufficient docstring; use context and docstring above.';

  const prompt = `
    Generate multiple BDD test cases in Gherkin format (using Feature, Scenario, Given, When, Then) for the provided React component. The tests must:
    - Describe the behavior of the component in a human-readable way, focusing on user interactions and expected outcomes.
    - Include at least two positive scenarios (successful cases) and two negative scenarios (failure cases) under a single Feature.
    - Use the complete URL in Given steps by combining the base URL and route from the context (e.g., if Base URL is "${baseUrl}" and Route is "/dashboard", use "I am on the dashboard page at ${baseUrl}/dashboard").
    - If the application involves preconditions or specific interactions (e.g., login, data submission):
      - Use the provided "additional_info" to incorporate relevant details into the test steps (e.g., credentials for login, account info for transfers, or minor design changes).
      - For components requiring login (check context for 'Requires Login: true'), include login steps before proceeding:
        - Start with "Given I am on the login page at ${baseUrl}/".
        - Use "additional_info" to specify preconditions or inputs (e.g., "And I enter the provided credentials" or "And I use the provided account details").
        - Include appropriate actions (e.g., "And I click the 'Login' button").
        - Then proceed to "And I am on the <component> page at ${baseUrl}/<route>".
      - For other interactions (e.g., form submission, navigation), adapt "additional_info" as needed.
    - If the component is the landing page (e.g., identified as 'Is Landing Page: true'):
      - Include positive scenarios (e.g., successful action with valid inputs from "additional_info") and negative scenarios (e.g., invalid or missing inputs).
      - Reference UI elements generically (e.g., "field", "button") and verify outcomes (e.g., redirection, messages).
    - If the component is not the landing page:
      - Include positive scenarios (e.g., successful navigation, submission) and negative scenarios (e.g., invalid input, missing data).
      - Test core functionality with realistic examples based on context, docstring, and "additional_info".
    - Use provided context for structural details (e.g., routes, APIs, elements) derived from the cached design knowledge graph.
    - Incorporate any minor design changes or updates from "additional_info" without altering the base knowledge graph context.
    - Do not use specific attributes like data-testid or id for UI elements; keep descriptions generic.
    - Do not include implementation details or automation code.
    - Do not include markdown fences—output raw Gherkin text only.
    - Ensure proper indentation (2 spaces) and consistent Gherkin syntax.
    - Use the conversation history below to maintain consistency with previously generated tests.

    ${memoryString}

    ${contextSection}

    **Combined Knowledge Graph Context for Component:**
    ${componentContext}

    **Component Docstring:**
    ${docstring}

    **Base URL:**
    ${baseUrl}

    **Additional Info (Including Minor Design Changes):**
    ${additional_info}

    ${codeSection}
  `;

  console.log(`Generating BDD tests for ${componentName} with Gemini`);
  const result = await model.generateContent(prompt);
  const rawTestCode = result.response.text();
  const testCode = cleanTestCode(rawTestCode);

  // console.log(`Raw Gemini output for ${componentName}:`, JSON.stringify(rawTestCode));
  // console.log(`Cleaned test code for ${componentName}:`, JSON.stringify(testCode));

  const updatedHistory = [
    ...(memoryHistory || []),
    { role: 'Human', content: prompt },
    { role: 'AI', content: testCode }
  ];
  memoryHistoryStore[componentName] = updatedHistory;
  // console.log(`Updated memory history for ${componentName}:`, JSON.stringify(updatedHistory, null, 2));
  await saveMemoryHistory(memoryHistoryStore);

  return testCode;
}


async function generateTestsForComponents(componentFiles, designGraph, cache) {
  const orderedFiles = determineTestOrder(componentFiles, designGraph);
  console.log('Ordered files before processing:', orderedFiles);

  await fs.mkdir(FEATURES_DIR, { recursive: true });

  for (const file of orderedFiles) {
    const filePath = path.join(COMPONENTS_DIR, file);
    const stats = await fs.stat(filePath);
    const currentMtime = stats.mtimeMs; // Current modification time in milliseconds
    const code = await fs.readFile(filePath, 'utf-8');
    const componentName = path.basename(filePath, path.extname(filePath));
    const currentCode = await extractComponentCode(code, componentName);
    const docstring = await extractDocstring(code, componentName);

    // Generate embedding for current code (for logging purposes)
    const currentEmbedding = currentCode.trim() ? await generateEmbedding(currentCode) : null; // Null if code is empty

    const fileCache = cache.files[filePath] || { 
      componentName: null, 
      embedding: null, 
      code: '', 
      mtime: 0 
    };
    const cachedEmbedding = fileCache.embedding || null;
    const cachedComponentName = fileCache.componentName || '';
    const cachedMtime = fileCache.mtime || 0;
    const cachedCode = fileCache.code || '';

    // Log cosine similarity with safeguards
    if (currentEmbedding && cachedEmbedding) {
      const isValidVector = (vec) => vec && vec.length > 0 && vec.some(v => v !== 0); // Check non-zero vector
      if (isValidVector(currentEmbedding) && isValidVector(cachedEmbedding)) {
        const similarity = cosineSimilarity(currentEmbedding, cachedEmbedding);
        console.log(`Cosine similarity for ${componentName}: ${similarity}`);
      } else {
        console.log(`Cosine similarity for ${componentName}: Invalid - one or both embeddings are zero vectors`);
      }
    } else {
      console.log(`Cosine similarity for ${componentName}: Not computed - ${!currentEmbedding ? 'current' : 'cached'} embedding missing`);
    }

    let generatedTest;
    const hasFileChanged = currentMtime > cachedMtime; // Timestamp check
    const hasCodeChanged = currentCode !== cachedCode; // Simple string comparison for code change

    if (hasFileChanged && (hasCodeChanged || !fileCache.code || cachedComponentName !== componentName)) {
      console.log(`Generating new test for ${componentName} due to:`);
      if (hasFileChanged) console.log(`- File change (mtime: ${currentMtime} vs cached: ${cachedMtime})`);
      if (hasCodeChanged) console.log(`- Code content change`);
      if (!fileCache.code) console.log(`- New file`);
      if (cachedComponentName !== componentName) console.log(`- Rename from ${cachedComponentName} to ${componentName}`);

      // Remove old feature files for this component
      const existingFeatureFiles = (await fs.readdir(FEATURES_DIR))
        .filter(f => f.startsWith(`${componentName.toLowerCase()}-`) && f.endsWith('.feature'));
      for (const oldFile of existingFeatureFiles) {
        const oldFilePath = path.join(FEATURES_DIR, oldFile);
        await fs.unlink(oldFilePath);
        console.log(`Removed old feature file: ${oldFilePath}`);
      }

      const similarContext = null; // Commented out retrieveSimilarContext
      const codeGraph = await buildCodeKnowledgeGraph(filePath, code, componentName, cache);
      const combinedGraph = mergeKnowledgeGraphs(designGraph, codeGraph, componentName);
      const componentContext = getComponentContext(combinedGraph, componentName);
      generatedTest = await generateComponentTest(currentCode, componentContext, componentName, similarContext, combinedGraph.baseUrl, docstring);
      cache.files[filePath] = { 
        componentName, 
        embedding: currentEmbedding, 
        code: currentCode, 
        mtime: currentMtime 
      };
      cache.tests[filePath] = generatedTest;
    } else {
      console.log(`Using cached test for ${componentName} (no significant code changes or timestamp unchanged: mtime ${cachedMtime})`);
      generatedTest = cache.tests[filePath];
    }

    if (!generatedTest || typeof generatedTest !== 'string' || generatedTest.trim() === '') {
      throw new Error(`Generated test for ${componentName} is invalid or empty`);
    }

    const featureFiles = splitGherkinIntoFeatures(generatedTest, componentName);
    for (const { fileName, content } of featureFiles) {
      const featureFilePath = path.join(FEATURES_DIR, fileName);
      await fs.writeFile(featureFilePath, content);
      console.log(`Generated BDD test saved at ${featureFilePath}`);
    }
  }

  await saveCache(cache);
}

async function generateTests() {
  try {
    console.log('Validating provided paths...');
    await validatePaths();

    console.log('Initializing models...');
    await initializeModels();

    console.log('Loading cache...');
    const cache = await loadCache();

    console.log('Retrieving or building design knowledge graph...');
    let designGraph;
    const designCache = cache.knowledgeGraph.design || {};
    const cachedDesignGraph = DESIGN_PDF_PATH ? designCache[DESIGN_PDF_PATH]?.graph : Object.values(designCache)[0]?.graph; // Use first available if no PDF

    if (DESIGN_PDF_PATH) {
      console.log(`Building design knowledge graph from ${DESIGN_PDF_PATH}`);
      designGraph = await buildDesignKnowledgeGraph(DESIGN_PDF_PATH, cache);
    } else if (cachedDesignGraph) {
      console.log('Using cached design knowledge graph');
      designGraph = cachedDesignGraph;
    } else {
      console.error('Error: No design PDF provided and no design knowledge graph found in cache');
      console.error('Cache state:', JSON.stringify(cache.knowledgeGraph, null, 2));
      process.exit(1);
    }

    console.log('Scanning components directory...');
    const componentFiles = (await fs.readdir(COMPONENTS_DIR)).filter(file => 
      file.endsWith('.js') || file.endsWith('.jsx')
    );

    console.log('Generating BDD tests for all components...');
    await generateTestsForComponents(componentFiles, designGraph, cache);

    console.log('All BDD tests generated successfully in', FEATURES_DIR);
  } catch (error) {
    console.error('Error in test generation:', error);
    process.exit(1);
  }
}

generateTests();