# main.py
import asyncio
import logging
from engines.security.sast import SastSecurityEngine
from engines.testing.coverage import CoverageEngine
from models.report import ScanReport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAE-Quality")

async def audit_project(path: str):
    logger.info(f"--- 🛡️ Starting Enterprise Audit for: {path} ---")
    
    # 1. Run Security Scan
    sast = SastSecurityEngine(path)
    security_report = await sast.run()
    logger.info(f"Security Score: {security_report.score}")

    # 2. Run Coverage Scan
    testing = CoverageEngine(path)
    test_report = await testing.run()
    logger.info(f"Testing Score: {test_report.score}")

    # TODO: In future - Performance & Penetration tests here

    # Final Summary for Lab
    logger.info("Audit cycle completed. Reporting to RAE-Lab...")
    # Tutaj symulacja zapisu do labu
    return {
        "security": security_report.dict(),
        "testing": test_report.dict()
    }

async def main():
    projects = [
        "/home/print/cloud/billboard-marker",
        "/home/print/cloud/screenwatcher_project"
    ]
    for p in projects:
        await audit_project(p)

if __name__ == "__main__":
    asyncio.run(main())
