from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool
from oran_system.tools.custom_tool import CsvQueryTool
from dotenv import load_dotenv
import os


@CrewBase
class OranSystem():
    """OranSystem crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # Initialize tools
    def __init__(self):
        load_dotenv()
        self.directoryTool = DirectoryReadTool (directory=os.getenv("FOLDER_PATH"))
        self.csvQueryTool = CsvQueryTool()
        self.fileReadTool = FileReadTool()

    @agent
    def query_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['query_analyzer'],
            verbose=True
        )

    @agent
    def data_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyst'],
            tools=[self.directoryTool, self.csvQueryTool],
            verbose=True
        )
    
    @agent
    def response_formulator(self) -> Agent:
        return Agent(
            config=self.agents_config['response_formulator'],
            verbose=True
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
        )

    @crew
    def crew(self) -> Crew:
        """Creates the OranSystem crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
