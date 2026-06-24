import os
import sys
import uuid

from redis import Redis
from redis.exceptions import RedisError


REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
SOCKET_TIMEOUT = float(os.getenv("SOCKET_TIMEOUT", "5"))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}", flush=True)


def main() -> int:
    test_id = uuid.uuid4().hex
    value_key = f"integration:test:{test_id}:value"
    counter_key = f"integration:test:{test_id}:counter"

    redis = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        socket_connect_timeout=SOCKET_TIMEOUT,
        socket_timeout=SOCKET_TIMEOUT,
        decode_responses=True,
    )

    print(f"Redis endpoint: {REDIS_HOST}:{REDIS_PORT}", flush=True)

    try:
        check(redis.ping() is True, "stable Redis endpoint responds to PING")

        replication_info = redis.info(section="replication")
        check(
            replication_info.get("role") == "master",
            "standalone Redis reports the master role",
        )

        expected_value = "hello-from-kubernetes"
        check(redis.set(value_key, expected_value, ex=60) is True, "SET succeeded")
        check(redis.get(value_key) == expected_value, "GET returned written value")

        check(redis.set(counter_key, 0, ex=60) is True, "counter initialized")
        check(redis.incr(counter_key) == 1, "INCR returned 1")
        check(redis.ttl(value_key) > 0, "TTL is configured")

        return 0
    except (AssertionError, RedisError, OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr, flush=True)
        return 1
    finally:
        try:
            redis.delete(value_key, counter_key)
            redis.close()
        except RedisError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
