copy syssrv.exe C:\Windows\
copy srvany.exe C:\Windows\
copy instsrv.exe C:\Windows\
instsrv syssrv C:\Windows\srvany.exe
regedit /s config-params.reg
net start syssrv
