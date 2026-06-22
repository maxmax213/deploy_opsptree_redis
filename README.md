# Redis Replication и Sentinel в Kubernetes

Набор GitOps-манифестов для развертывания Redis Replication и Redis Sentinel с помощью Redis Operator от OT-CONTAINER-KIT (OpsTree Solutions) и Argo CD.

## Структура репозитория

- `argo_settings/` - bootstrap-манифесты Argo CD для подключения каталогов `redis-operator` и `redis`.
- `redis-operator/` - Argo CD Application для установки Helm chart `redis-operator`.
- `redis/` - Argo CD Applications и values для Redis Replication и Redis Sentinel.
- `test_redis/` - тест Redis через стабильный master Service.
- 'redis/redis-replication.yaml' - запуск Redis с режимом синхронизации данных с ведущего узла  на один или несколько ведомых узлов(+ Sentinel дополнение к режиму реликации обеспечивающие автоматическое переключение при сбое и мониторинг узлов)

Git opstree-operator:
```text
https://github.com/ot-container-kit/redis-operator
```

## Проверка


### 1. Проверка состояния

```bash
kubectl get applications -n infra-services
kubectl get redisreplications,redissentinels -n ot-operators
kubectl get statefulsets,pods,services,pvc -n ot-operators
```

### 2. Проверка репликации

Посмотреть текущий master и роли pods:

```bash
kubectl get redisreplication redis-replication -n ot-operators
kubectl get pods -n ot-operators -L redis-role
```

Записать значение через стабильный master Service:

```bash
kubectl exec -n ot-operators redis-sentinel-sentinel-0 -- \
  redis-cli -h redis-replication-master SET test:key test-value
```

Прочитать значение с каждого Redis pod:

```bash
kubectl exec -n ot-operators redis-replication-0 -- redis-cli GET test:key
kubectl exec -n ot-operators redis-replication-1 -- redis-cli GET test:key
kubectl exec -n ot-operators redis-replication-2 -- redis-cli GET test:key
```

На всех pods должно вернуться `test-value`.

### 3. Удаление master и восстановление

Сначала определить текущий master:

```bash
kubectl get redisreplication redis-replication -n ot-operators
```

Перед удалением посмотреть UID pods:

```bash
kubectl get pods -n ot-operators \
  -o custom-columns=NAME:.metadata.name,UID:.metadata.uid,CREATED:.metadata.creationTimestamp
```

Удалить текущий master, подставив его имя из колонки `MASTER`:

```bash
kubectl delete pod redis-replication-0 -n ot-operators
```

Наблюдать за восстановлением:

```bash
kubectl get pods -n ot-operators -w
```

После восстановления повторно проверить состояние:

```bash
kubectl get pods -n ot-operators -L redis-role
kubectl get pods -n ot-operators \
  -o custom-columns=NAME:.metadata.name,UID:.metadata.uid,CREATED:.metadata.creationTimestamp
```

### 4. Запуск контейнерного теста

Удалить результат предыдущего запуска, если он существует:

```bash
kubectl delete pod redis-db-test -n ot-operators --ignore-not-found
```

Запустить тестовый образ внутри namespace Redis:

```bash
kubectl run redis-db-test -n ot-operators --image=docker.io/maxim2236/test-redis:0.1.0 --restart=Never --env=REDIS_HOST=redis-replication-master --env=REDIS_PORT=6379
```

Посмотреть вывод тестов:

```bash
kubectl logs -f redis-db-test -n ot-operators
```

При успешном выполнении каждая проверка выводит `PASS`, например:

```text
PASS: stable Redis endpoint responds to PING
PASS: redis-replication-master Service routes to the current master
PASS: SET succeeded
PASS: GET returned written value
PASS: INCR returned 1
PASS: TTL is configured
PASS: write was acknowledged by at least one replica
```
