import time

class ProviderHealth:

    def __init__(self):
        self._failures = {}
        self._cooldown = 60

    def record_failure(self, provider):
        self._failures[provider] = time.time()

    def is_available(self, provider):
        last = self._failures.get(provider)
        if not last:
            return True
        return (time.time() - last) > self._cooldown