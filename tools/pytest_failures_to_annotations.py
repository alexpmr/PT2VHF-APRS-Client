"""Publica cada teste com falha do relatório JUnit como anotação do GitHub
Actions (::error), legível pela API sem baixar o log completo do job."""
import sys
import xml.etree.ElementTree as ET


def main(path: str) -> int:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        print(f"::warning::Relatório JUnit indisponível: {exc}")
        return 0
    count = 0
    for case in root.iter("testcase"):
        for problem in list(case.findall("failure")) + list(case.findall("error")):
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            detail = (problem.get("message") or problem.text or "").strip().replace("\r", "")
            detail = detail.replace("%", "%25").replace("\n", "%0A")[:1500]
            print(f"::error title={name}::{detail}")
            count += 1
    print(f"{count} teste(s) com falha reportado(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "pytest-report.xml"))
