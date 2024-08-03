setlocal EnableDelayedExpansion

:: 创建虚拟环境
python -m venv venv

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 安装依赖
pip install -r requirements.txt

endlocal