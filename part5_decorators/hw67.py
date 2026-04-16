import json
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(
        self,
        func_name: str,
        block_time: datetime,
    ):
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


@dataclass
class BreakerState:
    block_time: datetime | None = None
    fail_count: int = 0


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int,
        time_to_recover: int,
        triggers_on: type[Exception],
    ):
        errors: list[ValueError] = []

        def validate_positive_int(data: object, message: str) -> None:
            if not isinstance(data, int) or isinstance(data, bool) or data <= 0:
                errors.append(ValueError(message))

        validate_positive_int(critical_count, INVALID_CRITICAL_COUNT)
        validate_positive_int(time_to_recover, INVALID_RECOVERY_TIME)

        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self._critical_count = critical_count
        self._time_to_recover = time_to_recover
        self._triggers_on = triggers_on

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        func_name: str = f"{func.__module__}.{func.__name__}"
        state = BreakerState()

        def raise_if_blocked() -> None:
            if state.block_time is None:
                return

            if (datetime.now(UTC) - state.block_time).total_seconds() >= self._time_to_recover:
                state.block_time = None
                return

            raise BreakerError(func_name, state.block_time)

        def handle_trigger_error(error: Exception) -> None:
            state.fail_count += 1
            if state.fail_count < self._critical_count:
                return

            state.block_time = datetime.now(UTC)
            state.fail_count = 0
            raise BreakerError(func_name, state.block_time) from error

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            raise_if_blocked()

            try:
                result = func(*args, **kwargs)
            except self._triggers_on as error:
                handle_trigger_error(error)
                raise

            state.fail_count = 0
            return result

        return wrapper


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
