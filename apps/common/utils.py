import secrets
from enum import unique

from apps.common.models import BaseModel

def generate_unique_code(model:BaseModel, field: str) ->str:
    """
        Generate a unique code for a specified model and field.

        Args:
            model (BaseModel): The model class to check for uniqueness.
            field (str): The field name to check for uniqueness.

        Returns:
            str: A unique code.
    """
    allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    unique_code = "".join(secrets.choice(allowed_chars) for _ in range(12))
    similar_object_exists = model.objects.filter(**{field: unique_code}).exists()
    if not similar_object_exists:
        return unique_code
    return generate_unique_code(model, field)

def set_dict_attr(obj, data):
    for attr, value in data.items():
        setattr(obj, attr, value) # Ili obj.attr = value dlya kajdogo atributa
    return obj