# Redis Standalone в Kubernetes

GitOps-манифесты для развёртывания одного экземпляра Redis через Redis Operator от OT-CONTAINER-KIT и Argo CD.

В standalone-режиме запускается один Redis Pod без реплик, Sentinel и автоматического failover.

## Структура репозитория

- `argo_settings/` — корневые Argo CD Applications.
- `redis-operator/` — установка Redis Operator.
- `redis/` — Argo CD Application и Helm values для standalone Redis.
- `test_redis/` — контейнерный тест и дополнительный NodePort Service.

Redis Operator: <https://github.com/ot-container-kit/redis-operator>

## Проверка

### 1. Состояние Redis

```bash
kubectl get applications -n infra-services
kubectl get redis redis -n ot-operators
kubectl get statefulsets,pods,services,pvc -n ot-operators
```

Должен быть запущен один Pod `redis-0`.

### 2. PING, запись и чтение

```bash
kubectl exec -n ot-operators redis-0 -- redis-cli PING
kubectl exec -n ot-operators redis-0 -- redis-cli SET test:key test-value
kubectl exec -n ot-operators redis-0 -- redis-cli GET test:key
kubectl exec -n ot-operators redis-0 -- redis-cli DEL test:key
```

Ожидаемые результаты: `PONG`, `OK`, `test-value` и `1`.

### 3. Контейнерный тест

Удалить Pod от предыдущего запуска:

```bash
kubectl delete pod redis-db-test -n ot-operators --ignore-not-found
```

Запустить тест внутри namespace Redis:

```bash
kubectl run redis-db-test \
  -n ot-operators \
  --image=docker.io/maxim2236/test-redis:0.1.0 \
  --restart=Never \
  --env=REDIS_HOST=redis \
  --env=REDIS_PORT=6379
```

Посмотреть результат:

```bash
kubectl logs -f redis-db-test -n ot-operators
```

Успешный тест выводит:

```text
PASS: stable Redis endpoint responds to PING
PASS: standalone Redis reports the master role
PASS: SET succeeded
PASS: GET returned written value
PASS: counter initialized
PASS: INCR returned 1
PASS: TTL is configured
```
