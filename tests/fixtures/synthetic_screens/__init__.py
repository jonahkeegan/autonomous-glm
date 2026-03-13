"""Synthetic UI screenshot generator for golden dataset creation."""

from .generator import ScreenshotGenerator, generate_all_screenshots
from .templates import UITemplate, LoginTemplate, DashboardTemplate, FormTemplate, ListTemplate
from .issue_injectors import IssueInjector, IssueType

__all__ = [
    "ScreenshotGenerator",
    "generate_all_screenshots",
    "UITemplate",
    "LoginTemplate",
    "DashboardTemplate",
    "FormTemplate",
    "ListTemplate",
    "IssueInjector",
    "IssueType",
]