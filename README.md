# RAE-Quality: Autonomiczny Strażnik Jakości i Bezpieczeństwa 🛡️

RAE-Quality to moduł audytowy wewnątrz stosu RAE-Suite, zaprojektowany do ciągłego monitorowania, testowania i zabezpieczania kodu źródłowego produktów inżynieryjnych.

## 🛠️ Silniki Audytowe
Moduł wykorzystuje podejście wielowarstwowe (Multi-Engine) do oceny kodu:

1.  **SAST (Static Analysis)**: Zintegrowany silnik **Bandit** wykrywający luki bezpieczeństwa (np. SQL Injection, wycieki kluczy) w czasie rzeczywistym.
2.  **Coverage Engine**: Automatyczna analiza pokrycia testami za pomocą **Pytest-cov**. Wykrywa "martwe strefy" kodu, dla których Phoenix musi wygenerować testy.
3.  **DAST / Penetration**: Wykorzystuje moduł **RAE-Hive (Playwright)** do aktywnego testowania interfejsów i API pod kątem nieautoryzowanego dostępu.

## 🔄 Pętla Kaizen
RAE-Quality nie tylko raportuje błędy, ale aktywnie uczestniczy w ich naprawie:
1.  **Wykrycie**: Skaner znajduje słaby punkt.
2.  **Zgłoszenie**: Raport trafia do **RAE-Lab** i **RAE-Memory**.
3.  **Inicjacja Poprawki**: System wyzwala zadanie dla Phoenixa, aby naprawił błąd lub dopisał brakujące testy.

## 📊 Telemetria i Audyt
Pełna zgodność z **ISO 27001**. Każdy skan jest logowany z unikalnym identyfikatorem, a metryki jakości są przesyłane do centralnego systemu monitoringu.

---
**Module Status**: Production Ready
**Strategic Role**: Compliance & Risk Mitigation
