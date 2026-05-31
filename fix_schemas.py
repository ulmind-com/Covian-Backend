import re

path = "app/schemas/platform.py"
with open(path, "r") as f:
    content = f.read()

# Add imports
if "PyObjectId" not in content:
    content = content.replace(
        "from pydantic import BaseModel, EmailStr, Field",
        "from typing import Annotated\nfrom pydantic import BaseModel, EmailStr, Field, BeforeValidator\n\nPyObjectId = Annotated[str, BeforeValidator(str)]"
    )

# Replace id: str with id: PyObjectId
content = re.sub(r'(\s+)id:\s*str', r'\1id: PyObjectId', content)
content = re.sub(r'(\s+)company_id:\s*str', r'\1company_id: PyObjectId', content)
content = re.sub(r'(\s+)job_id:\s*str', r'\1job_id: PyObjectId', content)
content = re.sub(r'(\s+)candidate_id:\s*str', r'\1candidate_id: PyObjectId', content)
content = re.sub(r'(\s+)invoice_id:\s*str', r'\1invoice_id: PyObjectId', content)
content = re.sub(r'(\s+)lead_id:\s*str', r'\1lead_id: PyObjectId', content)

with open(path, "w") as f:
    f.write(content)
print("Updated platform.py")
