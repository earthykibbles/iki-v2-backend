from pydantic import BaseModel
from typing import List

class ActiveIngredient(BaseModel):
    name: str  # Name of the active ingredient
    strength: str  # Strength of the ingredient, e.g., 500mg
    unit: str  # Unit of measurement, e.g., mg, g, ml
    purpose: str  # What this ingredient does in the medicine
    potential_side_effects: List[str]  # Possible side effects of this ingredient

class Manufacturer(BaseModel):
    name: str  # Name of the manufacturer
    country: str  # Country of manufacture
    contact_email: str  # Manufacturer contact email

class Medicine(BaseModel):
    name: str  # Brand or generic name of the medicine
    active_ingredients: List[ActiveIngredient]  # List of active ingredients
    dosage_form: str  # Form of the medicine, e.g., tablet, syrup, injection
    route_of_administration: str  # How the medicine is administered, e.g., oral, IV, topical
    manufacturer: Manufacturer  # Manufacturer details
    indications: List[str]  # Medical conditions this medicine is used for
    contraindications: List[str]  # Conditions where the medicine should not be used
    side_effects: List[str]  # Possible side effects
    warnings: List[str]  # Important warnings and precautions
    storage_conditions: str  # Recommended storage conditions
    prescription_required: bool  # Whether a prescription is required to obtain this medicine
    mechanism_of_action: str  # How the medicine works in the body
    interactions: List[str]  # Possible drug or food interactions
    lifestyle_considerations: str  # Dietary, exercise, or activity considerations while taking the medicine
    overdose_risks: str  # Symptoms and risks of overdose
    patient_experience: str  # What a user might expect while taking this medicine
