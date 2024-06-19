import bs4


class ValidationError:
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column

    def __repr__(self): # pragma: no cover
        return f"Error at {self.line}:{self.column}: {self.message}"


class ValidationResult:
    def __init__(self, is_valid: bool, errors: list[ValidationError]):
        self._is_valid = is_valid
        self._errors = errors

    def __bool__(self):
        return self._is_valid

    @property
    def is_valid(self):
        return self._is_valid

    @property
    def errors(self):
        return self._errors

    @staticmethod
    def success():
        return ValidationResult(True, [])

    def add_node_error(self, message: str, node: bs4.Tag):
        self._errors.append(ValidationError(f"Error in {node}: {message}", node.sourceline, node.sourcepos))
        self._is_valid = False

    def __iadd__(self, other):
        is_valid = self.is_valid and other.is_valid
        errors = self.errors + other.errors
        return ValidationResult(is_valid, errors)

    def combine_with(self, other: 'ValidationResult'):
        return self.__iadd__(other)
