import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools.csv_tools import CsvRagTool
# from crewai_tools import CSVSearchTool

# Load environment variables
load_dotenv()

# O-RAN metrics guide to include in system prompts
ORAN_METRICS_GUIDE = """
# O-RAN Network Metrics Guide

## Cell Metrics:
- RRU.PrbUsedDl: Physical Resource Block utilization 
- availPrbDl: Available PRBs for downlink (higher values mean more available resources)
- nrCellIdentity: Cell identifier
- throughput: Overall cell throughput
- pdcpBytesDl: Downlink data volume
- pdcpBytesUl: Uplink data volume

## UE Metrics:
- RF.serving.RSRP: Signal strength (-80 to -60 dBm excellent, <-100 dBm poor)
- RF.serving.RSRQ: Signal quality (-10 to -5 dB excellent, <-15 dB poor)
- RF.serving.RSSINR: Signal-to-interference ratio (higher is better)
- DRB.UEThpDl: User downlink throughput
- RRU.PrbUsedDl: Resource utilization per UE
- targetTput: Target throughput for the UE
- Viavi.UE.anomalies: Binary indicator of issues (0 is normal, 1 indicates problems)
- ue-id: User equipment identifier
- nrCellIdentity: Cell the UE is connected to
"""

csv_tool = CsvRagTool(
    csv_path=["./wireless-network-simulator/cell_reports_csv", "./wireless-network-simulator/ue_reports_csv"]
)

# 1. Query Analyzer Agent
query_analyzer = Agent(
    role="Query Analyzer",
    goal="Understand user queries about O-RAN network performance and extract key parameters",
    backstory="""You are an expert in telecommunications and O-RAN networks. Your job is to analyze
    user questions about network performance and identify what specific information they're looking for,
    which step/timestamp they're interested in, and any specific cells or metrics mentioned.""",
    verbose=True,
    llm="gpt-4-mini",
    system_prompt=f"""
    You are an O-RAN Query Analyzer specialized in telecommunications network monitoring.

    Your primary job is to extract:
    1. The specific step number mentioned in the query (e.g., "step 5", "last step")
    2. The type of analysis requested (loaded cells, user connections, signal quality)
    3. Any specific cells or UEs mentioned

    Common O-RAN query types:
    - "What is the most loaded cell in step X?" → Looking for highest RRU.PrbUsedDl
    - "Which users are connected to cell X in step Y?" → Filter UEs by nrCellIdentity
    - "Which users have poor signal quality in step Z?" → Looking for low RF.serving.RSRP

    Always identify the specific step number, as this determines which data files to analyze.

    {ORAN_METRICS_GUIDE}
    """
)

# 2. Data Analyst Agent
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
    - Most loaded cell: Find cells with lowest availPrbDl values in cell data
    - UEs connected to cell X: Find UEs where nrCellIdentity matches cell ID in a specific step
    - X UEs with poor signal: Find UEs with lowest RF.serving.RSRP values 

    Always provide numerical values and specific identifiers in your findings.

    {ORAN_METRICS_GUIDE}
    """
)

# 3. Response Formulator Agent
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

