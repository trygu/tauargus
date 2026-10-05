// Per-namespace init entry points for the Tau-Argus pybind11 module.
// Each namespace gets its own translation unit so that the duplicate
// `IProgressListener` class (core vs. hitas, identical include guard) is
// never pulled into a single TU.

#ifndef TAUARGUS_BIND_INIT_H
#define TAUARGUS_BIND_INIT_H

#include <pybind11/pybind11.h>

void init_core(pybind11::module_ &m);
void init_hitas(pybind11::module_ &m);
void init_rounder(pybind11::module_ &m);

#endif  // TAUARGUS_BIND_INIT_H
