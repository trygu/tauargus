cmake_minimum_required(VERSION 3.16)
project(tauargus_python CXX)

set(CMAKE_CXX_STANDARD 11)

find_package(pybind11 CONFIG REQUIRED)

set(NATIVE_LIB_DIR ${CMAKE_SOURCE_DIR}/../../engine/build/lib)
set(NATIVE_CORE_SRC ${CMAKE_SOURCE_DIR}/../../engine/native/core/src)
set(NATIVE_CSP_SRC ${CMAKE_SOURCE_DIR}/../../engine/native/csp/src)
set(NATIVE_HITAS_SRC ${CMAKE_SOURCE_DIR}/../../engine/native/hitas/src)
set(NATIVE_ROUNDER_SRC ${CMAKE_SOURCE_DIR}/../../engine/native/rounder/src)

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
# `import pytauargus._tauargus` works both in dev and inside the wheel.
set(PKG_DIR ${CMAKE_SOURCE_DIR}/src/pytauargus)
set_target_properties(_tauargus PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${PKG_DIR}
    LIBRARY_OUTPUT_DIRECTORY_RELEASE ${PKG_DIR}
    BUILD_RPATH "${NATIVE_LIB_DIR};$ORIGIN"
    INSTALL_RPATH "@loader_path"
)

# Ship the runtime dylibs next to the extension so the wheel is self-contained.
# rounder links CRP (libCRP.dylib), so CRP must ship alongside it.
add_custom_command(TARGET _tauargus POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${NATIVE_LIB_DIR}/libtauargus_hitas.dylib
        ${NATIVE_LIB_DIR}/libtauargus_rounder.dylib
        ${NATIVE_LIB_DIR}/libtauargus_csp.dylib
        ${NATIVE_LIB_DIR}/libCRP.dylib
        ${PKG_DIR}
)

# Install into the wheel so `import pytauargus` works from an installed wheel
# (scikit-build-core runs `cmake --install` into the wheel staging dir).
install(TARGETS _tauargus LIBRARY DESTINATION pytauargus)
install(FILES
    ${NATIVE_LIB_DIR}/libtauargus_hitas.dylib
    ${NATIVE_LIB_DIR}/libtauargus_rounder.dylib
    ${NATIVE_LIB_DIR}/libtauargus_csp.dylib
    ${NATIVE_LIB_DIR}/libCRP.dylib
    DESTINATION pytauargus
)
