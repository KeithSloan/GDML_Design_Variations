# gdmlvar - Geant4 application for GDML design-variation studies
#
#   cmake -S g4app -B g4app/build -DCMAKE_BUILD_TYPE=Release
#   cmake --build g4app/build -j 8
#
# Geant4 must be built with GDML support (conda-forge's geant4 is).
cmake_minimum_required(VERSION 3.16)
project(gdmlvar CXX)

# In a conda environment, look for Geant4's dependencies (expat, xerces-c,
# CLHEP, ...) there first.  Otherwise CMake can pick the older copies in the
# macOS SDK or /usr, and find_package(Geant4) fails on their version.
if(DEFINED ENV{CONDA_PREFIX})
  list(PREPEND CMAKE_PREFIX_PATH "$ENV{CONDA_PREFIX}")
endif()

find_package(Geant4 REQUIRED gdml)
include(${Geant4_USE_FILE})

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(gdmlvar gdmlvar.cc ${sources} ${headers})
target_include_directories(gdmlvar PRIVATE ${PROJECT_SOURCE_DIR}/include)
target_link_libraries(gdmlvar ${Geant4_LIBRARIES})
