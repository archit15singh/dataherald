from abc import ABC, abstractmethod
from typing import List

from fastapi import BackgroundTasks

from dataherald.api.types.query import Query
from dataherald.api.types.requests import (
    NLGenerationRequest,
    PromptRequest,
    SQLGenerationRequest,
)
from dataherald.api.types.responses import (
    NLGenerationResponse,
    PromptResponse,
    SQLGenerationResponse,
)
from dataherald.config import Component
from dataherald.db_scanner.models.types import QueryHistory, TableDescription
from dataherald.sql_database.models.types import DatabaseConnection, SSHSettings
from dataherald.types import (
    CancelFineTuningRequest,
    DatabaseConnectionRequest,
    Finetuning,
    FineTuningRequest,
    GoldenSQL,
    GoldenSQLRequest,
    Instruction,
    InstructionRequest,
    ScannerRequest,
    TableDescriptionRequest,
    UpdateInstruction,
)


class API(Component, ABC):
    @abstractmethod
    def heartbeat(self) -> int:
        """Returns the current server time in nanoseconds to check if the server is alive"""
        pass

    @abstractmethod
    def scan_db(
        self, scanner_request: ScannerRequest, background_tasks: BackgroundTasks
    ) -> bool:
        pass

    @abstractmethod
    def create_database_connection(
        self, database_connection_request: DatabaseConnectionRequest
    ) -> DatabaseConnection:
        pass

    @abstractmethod
    def list_database_connections(self) -> list[DatabaseConnection]:
        pass

    @abstractmethod
    def update_database_connection(
        self,
        db_connection_id: str,
        database_connection_request: DatabaseConnectionRequest,
    ) -> DatabaseConnection:
        pass

    @abstractmethod
    def update_table_description(
        self,
        table_description_id: str,
        table_description_request: TableDescriptionRequest,
    ) -> TableDescription:
        pass

    @abstractmethod
    def list_table_descriptions(
        self, db_connection_id: str, table_name: str | None = None
    ) -> list[TableDescription]:
        pass

    @abstractmethod
    def get_table_description(self, table_description_id: str) -> TableDescription:
        pass

    @abstractmethod
    def create_prompt(self, prompt_request: PromptRequest) -> PromptResponse:
        pass

    @abstractmethod
    def add_golden_sqls(self, golden_sqls: List[GoldenSQLRequest]) -> List[GoldenSQL]:
        pass

    @abstractmethod
    def execute_sql_query(self, query: Query) -> tuple[str, dict]:
        pass

    @abstractmethod
    def get_query_history(self, db_connection_id: str) -> list[QueryHistory]:
        pass

    @abstractmethod
    def delete_golden_sql(self, golden_sql_id: str) -> dict:
        pass

    @abstractmethod
    def get_golden_sqls(
        self, db_connection_id: str = None, page: int = 1, limit: int = 10
    ) -> List[GoldenSQL]:
        pass

    @abstractmethod
    def add_instruction(self, instruction_request: InstructionRequest) -> Instruction:
        pass

    @abstractmethod
    def get_instructions(
        self, db_connection_id: str = None, page: int = 1, limit: int = 10
    ) -> List[Instruction]:
        pass

    @abstractmethod
    def delete_instruction(self, instruction_id: str) -> dict:
        pass

    @abstractmethod
    def update_instruction(
        self,
        instruction_id: str,
        instruction_request: UpdateInstruction,
    ) -> Instruction:
        pass

    @abstractmethod
    def create_finetuning_job(
        self, fine_tuning_request: FineTuningRequest, background_tasks: BackgroundTasks
    ) -> Finetuning:
        pass

    @abstractmethod
    def cancel_finetuning_job(
        self, cancel_fine_tuning_request: CancelFineTuningRequest
    ) -> Finetuning:
        pass

    @abstractmethod
    def get_finetuning_job(self, finetuning_job_id: str) -> Finetuning:
        pass

    @abstractmethod
    def create_sql_generation(
        self, prompt_id: str, sql_generation_request: SQLGenerationRequest
    ) -> SQLGenerationResponse:
        pass

    @abstractmethod
    def create_prompt_and_sql_generation(
        self, prompt: PromptRequest, sql_generation: SQLGenerationRequest
    ) -> SQLGenerationResponse:
        pass

    @abstractmethod
    def create_nl_generation(
        self, sql_generation_id: str, nl_generation_request: NLGenerationRequest
    ) -> NLGenerationResponse:
        pass

    @abstractmethod
    def create_sql_and_nl_generation(
        self,
        prompt_id: str,
        sql_generation: SQLGenerationRequest,
        nl_generation: NLGenerationRequest,
    ) -> NLGenerationResponse:
        pass

    def create_prompt_sql_and_nl_generation(
        self,
        prompt: PromptRequest,
        sql_generation: SQLGenerationRequest,
        nl_generation: NLGenerationRequest,
    ) -> NLGenerationResponse:
        pass
