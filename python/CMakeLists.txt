cmake_minimum_required(VERSION 3.16)
project(tauargus_python CXX)

set(CMAKE_CXX_STANDARD 11)

find_package(pybind11 CONFIG REQUIRED)

set(NATIVE_LIB_DIR ${CMAKE_SOURCE_DIR}/../native/build/lib)
set(NATIVE_CORE_SRC ${CMAKE_SOURCE_DIR}/../native/core/src)
set(NATIVE_CSP_SRC ${CMAKE_SOURCE_DIR}/../native/csp/src)
set(NATIVE_HITAS_SRC ${CMAKE_SOURCE_DIR}/../native/hitas/src)
set(NATIVE_ROUNDER_SRC ${CMAKE_SOURCE_DIR}/../native/rounder/src)

# Five translation units: the module entry point plus one TU per native
# namespace. Separate TUs keep the duplicate IProgressListener classes
# (core vs. hitas) from ever sharing a translation unit.
pybind11_add_module(_tauargus
    cpp/module.cpp
    cpp/bind_core.cpp
    cpp/bind_csp.cpp
    cpp/bind_hitas.cpp
    cpp/bind_rounder.cpp
)

target_include_directories(_tauargus
    PRIVATE
        ${CMAKE_SOURCE_DIR}/cpp
        ${NATIVE_CORE_SRC}
        ${NATIVE_CSP_SRC}
        ${NATIVE_HITAS_SRC}
        ${NATIVE_ROUNDER_SRC}
)

# Core is a static lib (code copied in). csp/hitas + rounder are shared
# dylibs (they pull in HiGHS transitively). csp is linked explicitly for
# the audit (TauAuditJj) entry point.
target_link_libraries(_tauargus PRIVATE
    ${NATIVE_LIB_DIR}/libtauargus_core.a
    ${NATIVE_LIB_DIR}/libtauargus_csp.dylib
    ${NATIVE_LIB_DIR}/libtauargus_hitas.dylib
    ${NATIVE_LIB_DIR}/libtauargus_rounder.dylib
)

# Output the extension straight into the python package dir so that a plain
# `import tauargus._tauargus` works both in dev and inside the wheel.
set(PKG_DIR ${CMAKE_SOURCE_DIR}/src/tauargus)
set_target_properties(_tauargus PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${PKG_DIR}
    LIBRARY_OUTPUT_DIRECTORY_RELEASE ${PKG_DIR}
    BUILD_RPATH "${NATIVE_LIB_DIR};$ORIGIN"
    INSTALL_RPATH "@loader_path"
)

# Ship the runtime dylibs next to the extension so the wheel is self-contained.
add_custom_command(TARGET _tauargus POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${NATIVE_LIB_DIR}/libtauargus_hitas.dylib
        ${NATIVE_LIB_DIR}/libtauargus_rounder.dylib
        ${NATIVE_LIB_DIR}/libtauargus_csp.dylib
        ${PKG_DIR}
)
