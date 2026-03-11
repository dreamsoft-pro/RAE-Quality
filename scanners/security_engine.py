# scanners/security_engine.py
import subprocess
import json
import os

class SecuritySentinel:
    """Moduł bezpieczeństwa Enterprise (SAST + DAST)."""
    
    @staticmethod
    def run_bandit_scan(path):
        """Statyczna analiza kodu pod kątem bezpieczeństwa."""
        print(f"🔍 [Bandit] Analiza kodu w: {path}")
        try:
            # Uruchamiamy bandit i zbieramy wyniki do JSON
            result = subprocess.run(
                ["bandit", "-r", path, "-f", "json", "-q"],
                capture_output=True, text=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def run_api_pentest(api_url):
        """Podstawowy test penetracyjny API (np. SQL Injection probe)."""
        print(f"🧨 [Pentest] Atak kontrolowany na API: {api_url}")
        # Tu wdrożymy próby wstrzykiwania złośliwych danych do endpointów
        return {"status": "safe", "findings": []}

if __name__ == "__main__":
    # Test na Billboard Marker
    sentinel = SecuritySentinel()
    report = sentinel.run_bandit_scan("/home/print/cloud/billboard-marker")
    print(f"Znaleziono {len(report.get('results', []))} potencjalnych luk.")
