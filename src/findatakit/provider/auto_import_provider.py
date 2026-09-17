# 自动扫描模块. include: 包含的模块名，None表示包含所有模块
# auto scan all modules in the package and import them if the module name is in the include list or None is passed
def auto_import_providers(package, include=None):
    import importlib
    import pkgutil

    pkg = importlib.import_module(package)

    for _, name, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        if include and not any(k in name for k in include):
            continue
        importlib.import_module(name)