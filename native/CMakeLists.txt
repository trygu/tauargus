# Tau-Argus — top-level native superbuild.
#
# Builds the five SDC engine modules in dependency order:
#   core    (static; shared data structures / utilities)
#   csp     (LP/MIP engine, HiGHS-backed)
#   hitas   (hierarchical table suppression; links csp)
#   crp     (controlled rounding, HiGHS-backed)
#   rounder (thin C++ dispatch over crp)
#
# All solver backends converge on the open-source HiGHS. Configure with the
# HiGHS CMake package path, e.g. on macOS Homebrew:
#
#   cmake -S native -B native/build \
#         -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs
#   cmake --build native/build -j

cmake_minimum_required(VERSION 3.16)
project(tauargus_native C CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Centralize build outputs: all shared/static libs in <build>/lib, binaries in
# <build>/bin. (Directory-scoped; inherited by the add_subdirectory calls below.)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Default HiGHS search hint (overridable via -DHighs_DIR).
if(NOT DEFINED Highs_DIR AND CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    find_program(BREW brew)
    if(BREW)
        execute_process(COMMAND ${BREW} --prefix
                        OUTPUT_VARIABLE _BREW_PREFIX
                        OUTPUT_STRIP_TRAILING_WHITESPACE)
        if(EXISTS "${_BREW_PREFIX}/lib/cmake/Highs")
            set(Highs_DIR "${_BREW_PREFIX}/lib/cmake/Highs")
        endif()
    endif()
endif()

add_subdirectory(core)
add_subdirectory(csp)
add_subdirectory(hitas)
add_subdirectory(crp)
add_subdirectory(rounder)
