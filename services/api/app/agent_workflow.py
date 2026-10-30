import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

from packages.repository_tools.repository_tools import read_file
from services.api.app.core.config import REPOSITORY_ROOT
from services.api.app.schemas.agent import CodePlan, ProposedPatch
from services.api.app.execution import execute_patch

from packages.repository_tools.context_builder import (
    collect_repository_context,
)

load_dotenv()


class CodingState(TypedDict, total=False):
    task: str
    source_code: str
    plan: dict
    patch: dict
    error: str
    execution: dict
    repository_context: dict


def get_model() -> ChatGroq:
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not configured.")

    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0,
    )


def analyze_repository(state: CodingState) -> dict:
    context = collect_repository_context(
        repository_root=REPOSITORY_ROOT,
        task=state["task"],
    )

    if not context["files"]:
        raise ValueError("No eligible repository files were found.")

    return {
        "source_code": context["files"][0]["content"],
        "repository_context": context,
    }


def plan_change(state: CodingState) -> dict:
    model = get_model().with_structured_output(CodePlan, method="json_mode",)

    context = state["repository_context"]
    context_text = "\n\n".join(
        f"--- FILE: {item['path']} ---\n{item['content']}"
        for item in context["files"]
    )

    result = model.invoke([
        (
            "system",
            "You are a software engineering planner. "
            "Analyze the supplied repository context and produce a concise plan. "
            "Return one JSON object with exactly these required keys: "
            "summary, files_to_inspect, steps, acceptance_criteria. "
            "files_to_inspect must be an array of repository-relative paths. "
            "Do not use files_to_modify or any alternative field names. "
            "Do not call tools. Do not claim that files have been changed or tested."
        ),
        (
            "human",
            f"Task:\n{state['task']}\n\n"
            f"Repository context:\n{context_text}\n\n"
            "Create the plan using the exact required schema."
        ),
    ])

    return {"plan": result.model_dump()}


def propose_patch(state: CodingState) -> dict:
    model = get_model().with_structured_output(ProposedPatch, method="json_mode",)

    context = state["repository_context"]

    context_text = "\n\n".join(
        f"--- FILE: {item['path']} ---\n{item['content']}"
        for item in context["files"]
    )

    result = model.invoke([
        (
            "system",
            "You are a careful coding agent. Return a valid JSON object "
            "matching the ProposedPatch schema with fields file_path, "
            "explanation, original_code, and proposed_code. "
            "Choose exactly one target file from the supplied repository context. "
            "The file_path must exactly match one supplied file path. "
            "The original_code must be a unique substring of that file's content. "
            "Make the smallest appropriate change. Do not include commentary "
            "outside the JSON object."
        ),
        (
            "human",
            f"Task:\n{state['task']}\n\n"
            f"Plan:\n{state['plan']}\n\n"
            f"Repository context:\n{context_text}\n\n"
            "Propose one minimal patch for the task."
        ),
    ])

    allowed_files = {
        item["path"]: item["content"]
        for item in state["repository_context"]["files"]
    }

    if result.file_path not in allowed_files:
        raise ValueError(
            "Patch target must be one of the inspected repository files."
        )

    target_source = allowed_files[result.file_path]

    if not result.original_code or target_source.count(result.original_code) != 1:
        raise ValueError(
            "Original code must match exactly one location in the target file."
        )

    if result.original_code == result.proposed_code:
        raise ValueError("Patch does not change the code.")

    return {"patch": result.model_dump()}


def build_graph():
    graph = StateGraph(CodingState)

    graph.add_node("analyze_repository", analyze_repository)
    graph.add_node("plan_change", plan_change)
    graph.add_node("propose_patch", propose_patch)

    graph.add_edge(START, "analyze_repository")
    graph.add_edge("analyze_repository", "plan_change")
    graph.add_edge("plan_change", "propose_patch")
    graph.add_edge("propose_patch", END)

    return graph.compile()

def execute_proposed_patch(state: CodingState) -> dict:
    patch = state["patch"]

    result = execute_patch(
        repository_root=REPOSITORY_ROOT,
        file_path=patch["file_path"],
        original_code=patch["original_code"],
        proposed_code=patch["proposed_code"],
        task=state["task"],
        plan=state.get("plan", {}),
        max_retries=2,
    )

    return {"execution": result}


def build_graph():
    graph = StateGraph(CodingState)

    graph.add_node("analyze_repository", analyze_repository)
    graph.add_node("plan_change", plan_change)
    graph.add_node("propose_patch", propose_patch)
    graph.add_node("execute_proposed_patch", execute_proposed_patch)

    graph.add_edge(START, "analyze_repository")
    graph.add_edge("analyze_repository", "plan_change")
    graph.add_edge("plan_change", "propose_patch")
    graph.add_edge("propose_patch", "execute_proposed_patch")
    graph.add_edge("execute_proposed_patch", END)

    return graph.compile()