@echo off
rem 定义循环间隔时间和监测的服务：
set secs=60
set srvname="jenkinsslave-D__jenkins"

echo.
echo ========================================
echo ==         查询计算机服务的状态，     ==
echo ==     每间隔%secs%秒种进行一次查询，     ==
echo ==     如发现其停止，则立即启动。     ==
echo ========================================
echo.
echo 此脚本监测的服务是：%srvname%
echo.

if %srvname%. == . goto end

:chkit
set svrst=0
for /F "tokens=1* delims= " %%a in ('net start') do if /I "%%a %%b" == %srvname% set svrst=1
if %svrst% == 0 net start %srvname%
set svrst=
rem 下面的命令用于延时，否则可能会导致cpu单个核心满载。
ping -n %secs% 127.0.0.1 > nul
goto chkit

:end
