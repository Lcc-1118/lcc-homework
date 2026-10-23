"""支持 `python -m warehouse_coop` 的入口。

等价于调用 main.main()。
"""

from warehouse_coop.main import main

if __name__ == "__main__":
    raise SystemExit(main())
