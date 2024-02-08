import logging
from typing import List, Tuple

from langchain.text_splitter import RecursiveCharacterTextSplitter
from overrides import override
from sql_metadata import Parser

from dataherald.config import System
from dataherald.context_store import ContextStore
from dataherald.repositories.golden_sqls import GoldenSQLRepository
from dataherald.repositories.instructions import InstructionRepository
from dataherald.types import ContextFile, GoldenSQL, GoldenSQLRequest, Prompt

logger = logging.getLogger(__name__)


class MalformedGoldenSQLError(Exception):
    pass


class DefaultContextStore(ContextStore):
    def __init__(self, system: System):
        super().__init__(system)

    @override
    def retrieve_context_for_question(
        self, prompt: Prompt, number_of_samples: int = 3
    ) -> Tuple[List[dict] | None, List[dict] | None]:
        logger.info(f"Getting context for {prompt.text}")
        closest_questions = self.vector_store.query(
            query_texts=[prompt.text],
            db_connection_id=prompt.db_connection_id,
            collection=self.golden_sql_collection,
            num_results=number_of_samples,
        )

        samples = []
        golden_sqls_repository = GoldenSQLRepository(self.db)
        for question in closest_questions:
            golden_sql = golden_sqls_repository.find_by_id(question["id"])
            if golden_sql is not None:
                samples.append(
                    {
                        "prompt_text": golden_sql.prompt_text,
                        "sql": golden_sql.sql,
                        "score": question["score"],
                    }
                )
        if len(samples) == 0:
            samples = None
        instructions = []
        instruction_repository = InstructionRepository(self.db)
        all_instructions = instruction_repository.find_all()
        for instruction in all_instructions:
            if instruction.db_connection_id == prompt.db_connection_id:
                instructions.append(
                    {
                        "instruction": instruction.instruction,
                    }
                )
        if len(instructions) == 0:
            instructions = None

        return samples, instructions

    @override
    def add_golden_sqls(self, golden_sqls: List[GoldenSQLRequest]) -> List[GoldenSQL]:
        """Creates embeddings of the questions and adds them to the VectorDB. Also adds the golden sqls to the DB"""
        golden_sqls_repository = GoldenSQLRepository(self.db)
        stored_golden_sqls = []
        for record in golden_sqls:
            try:
                Parser(record.sql).tables  # noqa: B018
            except Exception as e:
                raise MalformedGoldenSQLError(
                    f"SQL {record.sql} is malformed. Please check the syntax."
                ) from e
            prompt_text = record.prompt_text
            golden_sql = GoldenSQL(
                prompt_text=prompt_text,
                sql=record.sql,
                db_connection_id=record.db_connection_id,
                metadata=record.metadata,
            )
            stored_golden_sqls.append(golden_sqls_repository.insert(golden_sql))

        self.vector_store.add_records(stored_golden_sqls, self.golden_sql_collection)
        return stored_golden_sqls

    @override
    def remove_golden_sqls(self, ids: List) -> bool:
        """Removes the golden sqls from the DB and the VectorDB"""
        golden_sqls_repository = GoldenSQLRepository(self.db)
        for id in ids:
            self.vector_store.delete_record(
                collection=self.golden_sql_collection, id=id
            )
            deleted = golden_sqls_repository.delete_by_id(id)
            if deleted == 0:
                logger.warning(f"Golden record with id {id} not found")
        return True

    @override
    def add_context_file(self, context_file: ContextFile, content: str) -> bool:
        """Adds the context file to the DB"""
        logger.info(f"Adding context file {context_file.file_name}")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        texts = text_splitter.create_documents([content])
        logger.info(f"Number of chunks: {len(texts)}")
        for index, text in enumerate(texts):
            self.vector_store.add_record(
                text.page_content,
                context_file.db_connection_id,
                self.context_files_collection,
                metadata=[
                    {
                        "file_name": context_file.file_name,
                        "db_connection_id": context_file.db_connection_id,
                        "text": text.page_content,
                    }
                ],
                ids=[context_file.id + str(index)],
            )
        return True

    @override
    def delete_context_file(self, context_file: ContextFile) -> bool:
        """Deletes the context file from the DB"""
        self.vector_store.delete_record_by_metadata(
            collection=self.context_files_collection,
            metadata={"file_name": context_file.file_name},
        )
        return True

    @override
    def retrieve_context_files(self, prompt: Prompt, num_results: int = 3) -> str:
        """Retrieves the context files from the DB"""
        context_files = self.vector_store.query(
            query_texts=[prompt.text],
            db_connection_id=prompt.db_connection_id,
            collection=self.context_files_collection,
            num_results=num_results,
        )
        text_content = ""
        for context_file in context_files:
            text_content += f"{context_file['metadata']['text']}\n"
        return text_content
