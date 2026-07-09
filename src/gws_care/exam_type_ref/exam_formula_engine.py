"""Safe arithmetic formula evaluator for computed exam parameters.

Only allows: numeric literals, named variables, and the operators +  -  *  /  **  unary-  unary+
No function calls, no attribute access, no string operations.
"""

import ast


class FormulaEvaluationError(Exception):
    pass


class ExamFormulaEngine:
    """Evaluate parameter formulas using safe AST traversal (no eval/exec)."""

    _BINOP_MAP = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.Pow: lambda a, b: a ** b,
    }
    _UNOP_MAP = {
        ast.USub: lambda a: -a,
        ast.UAdd: lambda a: +a,
    }
    _ALLOWED_NODES = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd,
        ast.Load,  # ctx attribute of Name nodes
    )

    @classmethod
    def evaluate(cls, formula: str, context: dict[str, float]) -> float:
        """Evaluate formula with the given variable bindings.

        Args:
            formula: e.g. "hematocrite * 10 / globules_rouges"
            context: code → numeric value for all referenced parameters

        Returns:
            computed float

        Raises:
            FormulaEvaluationError
        """
        # Accept ^ as power operator (alias for **)
        normalized = formula.strip().replace("^", "**")
        try:
            tree = ast.parse(normalized, mode="eval")
        except SyntaxError as e:
            raise FormulaEvaluationError(f"Formule invalide : {e}") from e
        return float(cls._eval(tree.body, context))

    @classmethod
    def _eval(cls, node: ast.AST, ctx: dict[str, float]) -> float:
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise FormulaEvaluationError(f"Constante non numérique : {node.value!r}")
            return float(node.value)

        if isinstance(node, ast.Name):
            if node.id not in ctx:
                raise FormulaEvaluationError(f"Variable inconnue : '{node.id}'")
            val = ctx[node.id]
            if val is None:
                raise FormulaEvaluationError(f"Valeur manquante pour : '{node.id}'")
            return float(val)

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in cls._BINOP_MAP:
                raise FormulaEvaluationError(f"Opérateur non autorisé : {op_type.__name__}")
            left = cls._eval(node.left, ctx)
            right = cls._eval(node.right, ctx)
            if op_type is ast.Div and right == 0:
                raise FormulaEvaluationError("Division par zéro dans la formule")
            return cls._BINOP_MAP[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in cls._UNOP_MAP:
                raise FormulaEvaluationError(f"Opérateur unaire non autorisé : {op_type.__name__}")
            return cls._UNOP_MAP[op_type](cls._eval(node.operand, ctx))

        raise FormulaEvaluationError(f"Expression non autorisée : {type(node).__name__}")

    @classmethod
    def get_variable_codes(cls, formula: str) -> list[str]:
        """Return all variable names referenced in the formula."""
        try:
            tree = ast.parse(formula.strip(), mode="eval")
        except SyntaxError:
            return []
        return [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]

    @classmethod
    def validate(cls, formula: str, available_codes: list[str]) -> str | None:
        """Validate formula syntax and variable references.

        Returns an error message string, or None if the formula is valid.
        """
        if not formula.strip():
            return "La formule ne peut pas être vide."

        normalized = formula.strip().replace("^", "**")
        try:
            tree = ast.parse(normalized, mode="eval")
        except SyntaxError as e:
            return f"Syntaxe invalide : {e}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id not in available_codes:
                    hints = ", ".join(available_codes) if available_codes else "(aucun code défini)"
                    return f"Variable inconnue : '{node.id}'. Codes disponibles : {hints}"
            elif isinstance(node, ast.Constant):
                if not isinstance(node.value, (int, float)):
                    return f"Constante non numérique : {node.value!r}"
            elif not isinstance(node, cls._ALLOWED_NODES):
                return f"Expression non autorisée : {type(node).__name__}"

        # Dry-run with dummy values
        dummy = {code: 1.0 for code in available_codes}
        try:
            cls.evaluate(formula, dummy)
        except FormulaEvaluationError as exc:
            return str(exc)

        return None
