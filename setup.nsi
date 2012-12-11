; NSIS installer script for the MSP430 BSL Utility
;
; (C) 2012 Flying Camp Design
;
; All Rights Reserved.
;
; AUTHOR: Chris Wilson <cwilson@flyingcampdesign.com>
;
; Released under a BSD-style license (please see LICENSE)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Defines

!define APP_NAME "MSP430 BSL Utility"
!define APP_EXE "${APP_NAME}.exe"
!define APP_UNINSTALL_EXE "Uninstall.exe"
!define APP_ICON "ic.ico"
!define APP_VERSION "0.9.1"
!define APP_VERSION_MAJOR "0x0"
!define APP_VERSION_MINOR "0x9"
!define APP_LICENSE "LICENSE"
!define APP_COMMENTS ""
!define COMPANY "Flying Camp Design"
!define COMPANY_URL "http://www.flyingcampdesign.com"
!define SUPPORT_URL "http://www.flyingcampdesign.com/support.html"
!define UPDATE_URL "http://www.flyingcampdesign.com/msp430-bsl-utility.html"
!define ABOUT_URL "http://www.flyingcampdesign.com/msp430-bsl-utility.html"
!define NOMODIFY "0x1"
!define NOREPAIR "0x1"
!define DIST_DIR "dist"
!define DOC_DIR "docs"
!define USER_GUIDE "UserGuide.html"
!define HEADER_IMAGE "resources\fcd_nsis_header.bmp"
!define WELCOME_FINISH_IMAGE "resources\fcd_nsis_wf.bmp"
!define INSTALLER_VERSION "${APP_VERSION}.0"
!define INSTALLER_ICON "resources\setup.ico"
!define INSTALLER_OUTDIR "nsis"

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Variables

Var StartMenuFolder
Var SizeOfInstall

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; General settings

; Use custom .onGUIInit
!define MUI_CUSTOMFUNCTION_GUIINIT myGUIInit

; Include a function library that includes a file/directory size reporting command
!include "FileFunc.nsh" ; for ${GetSize} for EstimatedSize registry entry

; Use Modern UI 2
!include MUI2.nsh

; Use lzma compression
SetCompressor lzma

; Set UAC level to admin (for Windows Vista and 7)
RequestExecutionLevel admin

; Do a CRC check
CRCCheck On

; Application name
Name "${APP_NAME} ${APP_VERSION}"

; Output file name
OutFile "${INSTALLER_OUTDIR}\msp430_bsl_utility_setup_${APP_VERSION}.exe"

; Default installation directory
InstallDir "$PROGRAMFILES\${COMPANY}\${APP_NAME} ${APP_VERSION}"

;Get installation folder from registry if available
InstallDirRegKey HKLM "Software\${COMPANY}\${APP_NAME} ${APP_VERSION}" ""

; Set COMPANY name
BrandingText "${COMPANY}"

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; MUI settings

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_ICON "${INSTALLER_ICON}"
!define MUI_UNICON "${INSTALLER_ICON}"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP ${HEADER_IMAGE}
!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH
!define MUI_HEADERIMAGE_RIGHT
!define MUI_WELCOMEFINISHPAGE_BITMAP ${WELCOME_FINISH_IMAGE}

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; MUI pages

; Install
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE ${APP_LICENSE}
!insertmacro MUI_PAGE_DIRECTORY
!define MUI_STARTMENUPAGE_REGISTRY_ROOT HKLM
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\${COMPANY}\${APP_NAME} ${APP_VERSION}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!insertmacro MUI_PAGE_FINISH

; Uninstall
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; MUI languages

!insertmacro MUI_LANGUAGE "English"

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Version information

VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "${APP_NAME}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "Comments" "${APP_COMMENTS}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "${COMPANY}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalCopyright" "(C) ${COMPANY}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "${APP_NAME} Setup"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "${APP_VERSION}"
VIProductVersion "${INSTALLER_VERSION}"

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Install

Section "Install" install_section_id

  ; Install for all users
  SetShellVarContext all
  
  ; Install Files
  SetOutPath "$INSTDIR"
  
  ; Store installation folder in registry
  WriteRegStr HKLM "Software\${COMPANY}\${APP_NAME} ${APP_VERSION}" "" $INSTDIR
  
  ; Let installer set compression
  SetCompress Auto
  
  ; Allow file overwrites
  SetOverwrite on
  
  ; Install all files in DIST_DIR
  File /r "${DIST_DIR}\*"
  
  ; Install docs
  SetOutPath "$INSTDIR\${DOC_DIR}"
  File "${DOC_DIR}\${USER_GUIDE}"
  SetOutPath "$INSTDIR"
  
  ; Write the uninstall keys to registry
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "DisplayName" "${APP_NAME} ${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "UninstallString" "$INSTDIR\${APP_UNINSTALL_EXE}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "DisplayIcon" "$INSTDIR\${APP_ICON}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "Publisher" "${COMPANY}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "HelpLink" "${SUPPORT_URL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "URLUpdateInfo" "${UPDATE_URL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "URLInfoAbout" "${ABOUT_URL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "DisplayVersion" "${APP_VERSION}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "VersionMajor" "${APP_VERSION_MAJOR}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "VersionMinor" "${APP_VERSION_MINOR}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "EstimatedSize" "$SizeOfInstall"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "NoModify" ${NOMODIFY}
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}" "NoRepair" ${NOREPAIR}
  
  ; Create the uninstaller
  WriteUninstaller "${APP_UNINSTALL_EXE}"

  ; Install start menu folder
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    ;Create shortcuts
    CreateDirectory "$SMPROGRAMS\${COMPANY}\$StartMenuFolder"
    CreateDirectory "$SMPROGRAMS\${COMPANY}\$StartMenuFolder\${DOC_DIR}"
;    CreateShortCut "$SMPROGRAMS\${COMPANY}\$StartMenuFolder\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_ICON}" 0
    CreateShortCut "$SMPROGRAMS\${COMPANY}\$StartMenuFolder\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortCut "$SMPROGRAMS\${COMPANY}\$StartMenuFolder\${DOC_DIR}\Users Guide.lnk" "$INSTDIR\${DOC_DIR}\${USER_GUIDE}"
    CreateShortCut "$SMPROGRAMS\${COMPANY}\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\${APP_UNINSTALL_EXE}"
  !insertmacro MUI_STARTMENU_WRITE_END

SectionEnd

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Uninstall

Section "Uninstall" uninstall_section_id

  ; Uninstall for all users
  SetShellVarContext all
  
  ; Delete start menu folder
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  RMDir /r "$SMPROGRAMS\${COMPANY}\$StartMenuFolder"
  
  ; Delete unistall registry entries
  DeleteRegKey HKLM "SOFTWARE\${COMPANY}\${APP_NAME} ${APP_VERSION}"
  DeleteRegKey HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME} ${APP_VERSION}"
  
  ; Delete the application directory
  RMDir /r "$INSTDIR"
  
SectionEnd

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Functions

Function myGUIInit

  ; Get size of install section
  SectionGetSize ${install_section_id} $SizeOfInstall
  
  ; Convert size to DWORD
  IntFmt $SizeOfInstall "0x%08X" "$SizeOfInstall"

FunctionEnd
