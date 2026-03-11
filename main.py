# main.py
import asyncio
import logging
import time
from engines.security.sast import SastSecurityEngine
from engines.testing.coverage import CoverageEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAE-Quality")

async def audit_project(path: str):
    logger.info(f"--- 🛡️ Auditing: {path} ---")
    try:
        sast = SastSecurityEngine(path)
        await sast.run()
        testing = CoverageEngine(path)
        await testing.run()
    except Exception as e:
        logger.error(f"Audit failed for {path}: {e}")

async def daemon_loop():
    projects = ["/home/print/cloud/billboard-marker", "/home/print/cloud/screenwatcher_project"]
    logger.info("🚀 RAE-Quality Sentinel ACTIVE (Kaizen Loop)")
    while True:
        for p in projects:
            await audit_project(p)
        logger.info("☕ Audit cycle complete. Sleeping for 1 hour...")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(daemon_loop())
