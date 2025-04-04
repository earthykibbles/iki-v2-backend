from typing import List, Optional
from pydantic import BaseModel

# Define a nested Pydantic model for management strategies
class ManagementStrategy(BaseModel):
    strategy_name: str  # Name of the management strategy
    strategy_description: str  # Description of the strategy
 
# Define a nested Pydantic model for diagnostic tests
class DiagnosticTest(BaseModel):
    test_name: str  # Name of the diagnostic test
    test_description: str  # Description of what the test detects

# Define a nested Pydantic model for support groups/resources
class SupportGroupResource(BaseModel):
    resource_name: str  # Name of the support group or resource
    resource_link: str  # Link to the resource or website

# Define the main Pydantic model for the chronic condition
class ChronicCondition(BaseModel):
    condition_name: str  # Name of the chronic condition
    condition_description: str  # Brief description of the condition
    common_symptoms: List[str]  # List of common symptoms
    severity_level: str  # Severity level (e.g., "Mild", "Moderate", "Severe")
    management_strategies: List[ManagementStrategy]  # List of management strategies
    average_affected_age: Optional[int]  # Average age affected (optional)
    condition_prevalence: Optional[str] # Prevalence (optional)
    risk_factors: List[str]  # List of risk factors
    diagnostic_tests: List[DiagnosticTest]  # List of diagnostic tests
    possible_complications: List[str]  # List of possible complications
    preventive_measures: List[str]  # List of preventive measures
    recommended_specialists: List[str]  # List of recommended specialists
    common_treatments: List[str]  # List of common treatments
    support_groups_resources: List[SupportGroupResource]  # List of support groups/resources (optional)