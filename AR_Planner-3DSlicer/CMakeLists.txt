cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(PedicleScrewPlacement_ARPlanner)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/ARforSpinalScrews")
set(EXTENSION_CATEGORY "PedicleScrewPlacementPlanner")
set(EXTENSION_CONTRIBUTORS "Alicia Pose (UC3M)")
set(EXTENSION_DESCRIPTION "Connect 3D slicer to your HoloLens 2 through OpenIGTLink device and share information about transforms and images back and forth.
Use this module for surgical planning of pedicular screws placement.")
set(EXTENSION_ICONURL "https://www.example.com/Slicer/Extensions/ARforSpinalScrews.png")
set(EXTENSION_SCREENSHOTURLS "https://www.example.com/Slicer/Extensions/ARforSpinalScrews/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(AR_Planner)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
