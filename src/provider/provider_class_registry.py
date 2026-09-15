from src.provider.provider import Provider


class ProviderClassRegistry:
    _classes: list[Provider]  = []

    @classmethod
    def register(cls, provider_cls: Provider):
        cls._classes.append(provider_cls)

    @classmethod
    def get_all(cls) -> list[Provider]:
        return list(cls._classes)


def register_provider(provider_cls: Provider):
    ProviderClassRegistry.register(provider_cls)
    return provider_cls