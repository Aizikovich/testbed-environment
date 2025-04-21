from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import FileReadTool

@CrewBase
class OranSystem():
    """OranSystem crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # Initialize tools
    def __init__(self):
        self.file_tool = FileReadTool(
            file_paths=["./wireless-network-simulator/cell_reports_csv", "./wireless-network-simulator/ue_reports_csv"]
        )

    @agent
    def query_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['query_analyzer'],
            verbose=True,
            llm="gpt-4o-mini"
        )

    @agent
    def data_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyst'],
            tools=[self.file_tool],
            verbose=True,
            llm="gpt-4o-mini"
        )
    
    @agent
    def response_formulator(self) -> Agent:
        return Agent(
            config=self.agents_config['response_formulator'],
            verbose=True,
            llm="gpt-4o-mini"
        )

    @task
    def analyze_query_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_query_task']
        )

    @task
    def analyze_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_data_task']
        )

    @task
    def formulate_response_task(self) -> Task:
        return Task(
            config=self.tasks_config['formulate_response_task'],
            # output_file='oran_analysis_report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the OranSystem crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=2
        )
