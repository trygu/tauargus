// Tau-Argus native engine — pybind11 module entry point.
// The three binding namespaces are defined in separate translation units
// (see bind_core.cpp / bind_hitas.cpp / bind_rounder.cpp) so that the
// duplicate `IProgressListener` classes (core vs. hitas) never collide.

#include <pybind11/pybind11.h>

#include "init_decls.h"

namespace py = pybind11;

PYBIND11_MODULE(_tauargus, m) {
    m.doc() = "Tau-Argus native SDC engine (HiGHS-backed)";
    init_core(m);
    init_csp(m);
    init_hitas(m);
    init_rounder(m);
}
