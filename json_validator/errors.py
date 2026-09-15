from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationError:
    """A JSON Pointer path identifies a value; syntax errors also carry source coordinates."""

    message: str
    path: str = ""
    line: int | None = None
    column: int | None = None


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def __bool__(self) -> bool:
        return self.is_valid
