from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import CsvRagTool

# Load environment variables
load_dotenv()

# O-RAN metrics guide 
ORAN_METRICS_GUIDE = """
# O-RAN Network Metrics Guide

## Cell Metrics:
- availPrbDl: Available PRBs (Physical Resource Block) for downlink (lower values indicate higher cell load/utilization)
- throughput: Overall cell throughput in Mbps (higher values indicate cells handling more data)
- pdcpBytesDl: Downlink data volume (matches throughput, indicates data traffic)
- nrCellIdentity: Cell identifier 
- x, y: Geographic coordinates of the cell location

## UE Metrics:
- RF.serving.RSRP: Reference Signals Received Power. Signal strength (higher values are better)
- RF.serving.RSSINR: Signal-to-Interference-plus-Noise Ratio (higher values indicate better signal quality)
- RRU.PrbUsedDl: Resource utilization per UE (higher values indicate more active users)
- DRB.UEThpDl: User downlink throughput (actual data speeds experienced)
- Viavi.UE.anomalies: Binary indicator of issues (0 is normal, 1 indicates problems)
- nrCellIdentity: Cell the UE is connected to
- ue-id: User identifier 
- nbCellIdentity_0 through nbCellIdentity_4: Identifiers for neighboring cells detected by the UE
- rsrp_nb0 through rsrp_nb4: RSRP values for each neighboring cell (signal strength from neighboring cells)
- rssinr_nb0 through rssinr_nb4: RSSINR values for each neighboring cell (signal quality relative to interference from neighboring cells)
- x, y: Geographic coordinates of the UE in the network layout
"""

csv_tool = CsvRagTool(
    csv_path=["./wireless-network-simulator/cell_reports_csv", "./wireless-network-simulator/ue_reports_csv"]
)

# Query Analyzer Agent
query_analyzer = Agent(
    role="Query Analyzer",
    goal="Understand user queries about O-RAN network performance and extract key parameters",
    backstory="""You are an expert in telecommunications and O-RAN networks. Your job is to analyze
    user questions about network performance and identify what specific information they're looking for,
    which step/timestamp they're interested in, and any specific cells or metrics mentioned.""",
    verbose=True,
    llm="gpt-4o-mini",
    system_prompt=f"""
    You are an O-RAN Query Analyzer specialized in telecommunications network monitoring.

    Your primary job is to extract:
    1. The specific step number mentioned in the query (e.g., "step 5", "last step")
    2. The type of analysis requested (loaded cells, user connections, signal quality)
    3. Any specific cells or UEs mentioned

    Common O-RAN query types and relevant metrics:
    - "What is the most loaded cell in step X?" 
    → Look for: availPrbDl (lower values indicate higher load), throughput, pdcpBytesDl

    - "Which users are connected to cell X in step Y?" 
    → Look for: nrCellIdentity in UE data matching the specified cell ID, along with ue-id

    - "Which users have poor signal quality in step Z?" 
    → Look for: RF.serving.RSRP (lowest values), RF.serving.RSSINR (lowest values), Viavi.UE.anomalies (value of 1)

    - "Which cell has the best coverage in step X?"
    → Look for: Number of connected UEs per cell, average RF.serving.RSRP values per cell

    - "Are there any users at risk of handover in step X?"
    → Look for: UEs where neighboring cell RSRP (rsrp_nb0 through rsrp_nb4) is close to serving cell RSRP

    - "Which cells are underutilized in step X?"
    → Look for: availPrbDl (highest values), throughput (lowest values), few connected UEs

    Always identify the specific step number, as this determines which data files to analyze.

    {ORAN_METRICS_GUIDE}
    """
)

# Data Analyst Agent
data_analyst = Agent(
    role="Data Analyst",
    goal="Search and analyze O-RAN network data to answer specific queries",
    backstory="""You are a data analyst specializing in telecommunications data. Your job is to
    search through O-RAN network logs (cell and UE metrics) to find the specific information
    requested by users, such as loaded cells, connected users, or signal quality issues.""",
    verbose=True,
    llm="gpt-4-mini",
    tools=[csv_tool],
    system_prompt=f"""
    You are an O-RAN Data Analyst who searches through network CSV data using the CSV RAG tool.

    To effectively use the CSV RAG tool:
    1. Be specific in your queries - mention exact column names (e.g., "RRU.PrbUsedDl", "RF.serving.RSRP")
    2. Include the step number in your search (e.g., "step 5")
    3. When working with cell data, look for "cell_reports_csv" in filenames
    4. When working with UE data, look for "ue_reports_csv" in filenames

    Common search tasks:
    - Most loaded cell: 
    * Find cells with lowest availPrbDl values in cell_report file
    * Also check highest throughput and pdcpBytesDl values
    * Consider the number of UEs connected to each cell

    - UEs connected to cell X: 
    * Find UEs where nrCellIdentity matches cell ID in ue_report file
    * Examine their RF.serving.RSRP values to assess connection quality
    * Check RRU.PrbUsedDl to identify resource consumption patterns

    - UEs with poor signal quality: 
    * Find UEs with lowest RF.serving.RSRP values in ue_reports files
    * Look for low RF.serving.RSSINR values 
    * Check if Viavi.UE.anomalies = 1 for these UEs

    - UEs at cell edge or handover candidates:
    * Find UEs where rsrp_nb0 through rsrp_nb4 values are close to RF.serving.RSRP
    * Look at nbCellIdentity_0 through nbCellIdentity_4 to identify potential target cells
    * Check geographic position (x,y) relative to cell locations

    - Underutilized cells:
    * Find cells with highest availPrbDl values
    * Compare with low throughput and pdcpBytesDl values
    * Count number of connected UEs

    Always provide numerical values and specific identifiers in your findings.

    {ORAN_METRICS_GUIDE}
    """
)

# Response Formulator Agent
response_formulator = Agent(
    role="Communication Expert",
    goal="Translate technical findings into clear, actionable insights for network operators",
    backstory="""You are a telecommunications consultant with expertise in explaining technical concepts in accessible language. 
    You take raw analysis from the Data Analyst and transform it into clear, concise responses that address the user's original query.
    You have deep knowledge of O-RAN networks and can put all metrics and findings in proper context.""",
    verbose=True,
    llm="gpt-4-mini",
    system_prompt=f"""
    You are an O-RAN Communication Expert who translates technical findings into clear, actionable insights.

    Your responses should:
    1. Begin with a direct answer to the original question
    2. Include the specific step that was analyzed
    3. Provide context about what the values mean
    4. Use plain language that network operators can quickly understand

    Focus on what's actionable - if you identify issues, briefly suggest possible causes.

    {ORAN_METRICS_GUIDE}
    """
)

# Define tasks

analyze_query_task = Task(
    description="""
    Analyze the user's query about O-RAN network performance. Identify what they want to know about the network.
    
    Specifically:
    1. What network metrics or information are they interested in? (cell load, user connections, signal quality, etc.)
    2. Which specific step or time period are they asking about?
    3. Are they asking about specific cells or users?
    
    Formulate a clear, specific question for the Data Analyst.
    
    The user query is: {query}
    """,
    expected_output="""A clear, specific question for the Data Analyst that identifies:
    1. The specific metrics or data needed
    2. The step number
    3. Any specific cells or UEs mentioned""",
    agent=query_analyzer
)

analyze_data_task = Task(
    description="""
    Using the CSV RAG tool, search through the O-RAN data to find the specific information
    requested in the query analysis.
    
    Be thorough in your analysis and provide specific data from the O-RAN logs that directly
    answers the query. Include relevant metrics and their values.
    
    Make sure to filter for the specific step mentioned in the query.
    
    The query analysis is: {query_analysis}
    """,
    expected_output="""Detailed findings from the O-RAN data, including specific metrics,
    values, and any relevant context about the network performance.""",
    agent=data_analyst
)

formulate_response_task = Task(
    description="""
    Create a clear, concise response that answers the user's original question about the O-RAN network.
    
    Your response should:
    1. Directly answer the user's question
    2. Explain any technical terms in simple language
    3. Provide context about why the information is important
    4. Be concise and easy to understand
    
    Original query: {query}
    Data analysis results: {data_analysis}
    """,
    expected_output="""A clear, concise response that directly answers the user's question about
    the O-RAN network in easy-to-understand language.""",
    agent=response_formulator
)

# Create the crew
oran_crew = Crew(
    agents=[query_analyzer, data_analyst, response_formulator],
    tasks=[analyze_query_task, analyze_data_task, formulate_response_task],
    verbose=2,
    process=Process.sequential
)

def analyze_oran_network(query):
    """Process a user query about the O-RAN network"""
    return oran_crew.kickoff(
        inputs={
            "query": query,
            "query_analysis": lambda inputs: inputs["analyze_query_task_output"],
            "data_analysis": lambda inputs: inputs["analyze_data_task_output"]
        }
    )

