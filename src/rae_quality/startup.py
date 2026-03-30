import httpx
import logging

CONTROL_PLANE_URL = "http://rae-suite:8009"

async def register_quality_department():
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{CONTROL_PLANE_URL}/api/v1/departments/register",
                json={
                    "agent_id": "quality-tribunal-1",
                    "department": "quality",
                    "role": "auditor",
                    "status": "active"
                }
            )
    except Exception as e:
        print(f"Registration failed: {e}")
