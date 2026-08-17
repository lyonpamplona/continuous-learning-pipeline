"""Modulo Scorer — avalia qualidade de SKILL.md com criterios objetivos."""

import re

import yaml


class Scorer:
    """Evaluates SKILL.md files with 10 objective criteria."""

    def __init__(self, min_pass: int = 70, max_size: int = 100000):
        self.min_pass = min_pass
        self.max_size = max_size

    def load_skill(self, path: str) -> dict:
        """Carregar um arquivo SKILL.md e parsear frontmatter + corpo."""
        with open(path) as f:
            content = f.read()

        match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return None

        fm = yaml.safe_load(match.group(1))
        body = content[match.end():]

        return {
            "frontmatter": fm,
            "body": body,
            "content": content,
            "path": path,
        }

    def score(self, skill_data: dict) -> dict:
        """Score a skill with 10 criteria. Returns score, decision, and checks."""
        checks = []
        total = 0

        fm = skill_data.get("frontmatter", {})
        body = skill_data.get("body", "")
        content = skill_data.get("content", "")

        # 1. Frontmatter completo (15 pts)
        required = ["name", "trigger", "description", "version"]
        has_all = all(k in fm for k in required)
        if has_all:
            total += 15
            checks.append("PASS: Frontmatter completo (name, trigger, description, version)")
        else:
            missing = [k for k in required if k not in fm]
            checks.append(f"FAIL: Frontmatter incompleto (faltando: {', '.join(missing)})")

        # 2. Description <= 60 chars (10 pts)
        desc = fm.get("description", "")
        if len(desc) <= 60:
            total += 10
            checks.append(f"PASS: Description tem {len(desc)} chars (max 60)")
        else:
            checks.append(f"FAIL: Description tem {len(desc)} chars (max 60)")

        # 3. Termina com ponto (5 pts)
        if desc.endswith("."):
            total += 5
            checks.append("PASS: Description termina com ponto")
        else:
            checks.append("FAIL: Description nao termina com ponto")

        # 4. Secoes essenciais (20 pts)
        essential_sections = ["When to Use", "Procedure"]
        found = [s for s in essential_sections if s.lower() in body.lower()]
        if len(found) >= 2:
            total += 20
            checks.append(f"PASS: Secoes essenciais encontradas ({', '.join(found)})")
        else:
            missing = [s for s in essential_sections if s.lower() not in body.lower()]
            checks.append(f"FAIL: Secoes essenciais faltando ({', '.join(missing)})")

        # 5. Procedure >= 3 passos (15 pts)
        procedure_match = re.search(r"## Procedure.*?(?:##|\Z)", body, re.DOTALL)
        if procedure_match:
            steps = re.findall(r"\d+\.", procedure_match.group())
            if len(steps) >= 3:
                total += 15
                checks.append(f"PASS: Procedure tem {len(steps)} passos (min 3)")
            else:
                checks.append(f"FAIL: Procedure tem {len(steps)} passos (min 3)")
        else:
            checks.append("FAIL: Procedure nao encontrada")

        # 6. Pitfalls >= 2 itens (10 pts)
        pitfalls_match = re.search(r"## Pitfalls.*?(?:##|\Z)", body, re.DOTALL)
        if pitfalls_match:
            items = re.findall(r"^[-*]\s+", pitfalls_match.group(), re.MULTILINE)
            if len(items) >= 2:
                total += 10
                checks.append(f"PASS: Pitfalls tem {len(items)} itens (min 2)")
            else:
                checks.append(f"FAIL: Pitfalls tem {len(items)} itens (min 2)")
        else:
            checks.append("FAIL: Pitfalls nao encontrada")

        # 7. Sem palavras de marketing (5 pts)
        marketing_words = ["revolutionary", "game-changing", "cutting-edge", "best-in-class"]
        body_lower = body.lower()
        found_marketing = [w for w in marketing_words if w in body_lower]
        if not found_marketing:
            total += 5
            checks.append("PASS: Sem palavras de marketing")
        else:
            checks.append(f"FAIL: Palavras de marketing encontradas ({', '.join(found_marketing)})")

        # 8. Size <= max_size (5 pts)
        size = len(content)
        if size <= self.max_size:
            total += 5
            checks.append(f"PASS: Tamanho {size} chars (max {self.max_size})")
        else:
            checks.append(f"FAIL: Tamanho {size} chars (max {self.max_size})")

        # 9. Author credita humano (5 pts)
        author = fm.get("author", "")
        if author and "CLP" not in author and "auto" not in author.lower():
            total += 5
            checks.append(f"PASS: Author credita humano ({author})")
        else:
            checks.append("FAIL: Author nao credita humano")

        # 10. Name valido (5 pts)
        name = fm.get("name", "")
        if name and re.match(r"^[a-z][a-z0-9-]*$", name):
            total += 5
            checks.append(f"PASS: Name valido ({name})")
        else:
            checks.append(f"FAIL: Name invalido ({name})")

        decision = "PASS" if total >= self.min_pass else "REJECT"

        return {
            "score": total,
            "decision": decision,
            "checks": checks,
            "min_pass": self.min_pass,
        }
