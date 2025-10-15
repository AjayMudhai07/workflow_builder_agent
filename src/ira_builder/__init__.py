"""
IRA Workflow Builder - Interactive Requirements Analyzer

A workflow builder system using Microsoft Agent Framework for generating
analysis code on CSV files based on user requirements.
"""

__version__ = "0.1.0"
__author__ = "IRA Team"

from ira_builder.agents import PlannerAgent

__all__ = [
    "PlannerAgent",
]
