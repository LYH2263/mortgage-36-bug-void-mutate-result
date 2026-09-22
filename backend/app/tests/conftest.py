import os
import tempfile

# 在导入任何 app 模块之前把数据库指到临时目录，避免污染开发数据。
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="mortgage-test-"))
