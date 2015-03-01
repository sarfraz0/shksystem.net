@ECHO OFF

python -c "import os,shutil; shutil.rmtree(os.path.join(os.environ['INDUS_HOME'], 'lib/net/shksystem'))"
XCOPY net %INDUS_HOME%\lib\net /S /E /Y
PAUSE