#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <vector>
#include <unordered_map>
#include <limits>
#include <stdexcept>
#include <cmath>
#include <algorithm>

namespace py = pybind11;

// ============================================================
// Standard CBC
// ============================================================
py::dict separate_cbc(
    py::array_t<double, py::array::c_style | py::array::forcecast> y,
    double theta,
    py::array_t<int, py::array::c_style | py::array::forcecast> indptr,
    py::array_t<int, py::array::c_style | py::array::forcecast> indices,
    py::array_t<double, py::array::c_style | py::array::forcecast> pval,
    py::array_t<double, py::array::c_style | py::array::forcecast> d,
    double tol = 1e-6
) {
    auto y_buf = y.unchecked<1>();
    auto indptr_buf = indptr.unchecked<1>();
    auto indices_buf = indices.unchecked<1>();
    auto pval_buf = pval.unchecked<1>();
    auto d_buf = d.unchecked<1>();

    const int nJ = static_cast<int>(d_buf.shape(0));
    const int nI = static_cast<int>(y_buf.shape(0));

    if (indptr_buf.shape(0) != nJ + 1) {
        throw std::runtime_error("indptr length must be |J| + 1.");
    }
    if (indices_buf.shape(0) != pval_buf.shape(0)) {
        throw std::runtime_error("indices and pval must have the same length.");
    }
    if (indptr_buf(nJ) != indices_buf.shape(0)) {
        throw std::runtime_error("indptr[-1] must equal the length of indices/pval.");
    }

    double lhs_val = 0.0;
    double const_term = 0.0;

    std::unordered_map<int, double> coeff_map;
    coeff_map.reserve(static_cast<size_t>(nI));

    for (int j = 0; j < nJ; ++j) {
        const int start = indptr_buf(j);
        const int end = indptr_buf(j + 1);

        if (start == end) {
            continue;
        }

        double min_val = std::numeric_limits<double>::infinity();
        int argmin_i = -1;
        double p_argmin = 0.0;
        double sum_val = 0.0;

        for (int k = start; k < end; ++k) {
            const int i = indices_buf(k);
            const double p_ij = pval_buf(k);
            const double y_i = y_buf(i);

            const double q_ij = 1.0 - (1.0 - p_ij) * y_i;

            if (q_ij < min_val) {
                min_val = q_ij;
                argmin_i = i;
                p_argmin = p_ij;
            }

            sum_val += p_ij * y_i;
        }

        const double d_j = d_buf(j);

        if (min_val < sum_val - tol) {
            // d_j * (1 - (1 - p_argmin) y_argmin)
            const_term += d_j;
            coeff_map[argmin_i] += -d_j * (1.0 - p_argmin);
            lhs_val += d_j * min_val;
        } else {
            // d_j * sum_i p_ij y_i
            for (int k = start; k < end; ++k) {
                const int i = indices_buf(k);
                const double c = d_j * pval_buf(k);
                coeff_map[i] += c;
                lhs_val += c * y_buf(i);
            }
        }
    }

    const bool violated = lhs_val < theta - tol;

    std::vector<int> idx;
    std::vector<double> coef;
    idx.reserve(coeff_map.size());
    coef.reserve(coeff_map.size());

    for (const auto& kv : coeff_map) {
        if (std::abs(kv.second) > 0.0) {
            idx.push_back(kv.first);
            coef.push_back(kv.second);
        }
    }

    py::dict out;
    out["violated"] = violated;
    out["lhs_val"] = lhs_val;
    out["const"] = const_term;
    out["idx"] = idx;
    out["coef"] = coef;
    return out;
}

// ============================================================
// CBC with one dual-degeneracy alternative cut
//
// Cut 1 (base): D_Q = empty set. Every degenerate customer
// remains in the sum-based term.
//
// Cut 2 (alternative): D_Q = D(y). For every degenerate
// customer, the sum-based term is REPLACED by the min-based
// term induced by another optimal dual solution.
//
// To reduce callback overhead, the alternative cut is built
// only if the base cut is violated and at least one eligible
// degenerate customer exists. The alternative is returned as
// a sparse delta relative to the base cut.
// ============================================================
py::dict separate_cbc_dual_degeneracy(
    py::array_t<double, py::array::c_style | py::array::forcecast> y,
    double theta,
    py::array_t<int, py::array::c_style | py::array::forcecast> indptr,
    py::array_t<int, py::array::c_style | py::array::forcecast> indices,
    py::array_t<double, py::array::c_style | py::array::forcecast> pval,
    py::array_t<double, py::array::c_style | py::array::forcecast> d,
    double tol = 1e-6,
    double duplicate_tol = 1e-8
) {
    auto y_buf = y.unchecked<1>();
    auto indptr_buf = indptr.unchecked<1>();
    auto indices_buf = indices.unchecked<1>();
    auto pval_buf = pval.unchecked<1>();
    auto d_buf = d.unchecked<1>();

    const int nJ = static_cast<int>(d_buf.shape(0));
    const int nI = static_cast<int>(y_buf.shape(0));
    const int nE = static_cast<int>(indices_buf.shape(0));

    if (indptr_buf.shape(0) != nJ + 1) {
        throw std::runtime_error("indptr length must be |J| + 1.");
    }
    if (indices_buf.shape(0) != pval_buf.shape(0)) {
        throw std::runtime_error("indices and pval must have the same length.");
    }
    if (indptr_buf(nJ) != nE) {
        throw std::runtime_error("indptr[-1] must equal the length of indices/pval.");
    }
    if (tol < 0.0 || duplicate_tol < 0.0) {
        throw std::runtime_error("tol and duplicate_tol must be nonnegative.");
    }

    struct DegenerateRecord {
        int start;
        int end;
        int argmin_i;
        double p_argmin;
        double d_j;
    };

    double base_lhs_val = 0.0;
    double base_const = 0.0;

    // Dense coefficient arrays are faster than hash maps here because |I|
    // is moderate and every callback already scans all customer edges.
    std::vector<double> base_coef(static_cast<size_t>(nI), 0.0);
    std::vector<DegenerateRecord> degenerate;
    degenerate.reserve(static_cast<size_t>(std::min(nJ, nI * 8)));

    for (int j = 0; j < nJ; ++j) {
        const int start = indptr_buf(j);
        const int end = indptr_buf(j + 1);

        if (start == end) {
            continue;
        }

        double min_val = std::numeric_limits<double>::infinity();
        int argmin_i = -1;
        double p_argmin = 0.0;

        double selected_min_val = std::numeric_limits<double>::infinity();
        int selected_argmin_i = -1;
        double selected_p_argmin = 0.0;

        double sum_val = 0.0;

        for (int k = start; k < end; ++k) {
            const int i = indices_buf(k);
            if (i < 0 || i >= nI) {
                throw std::runtime_error("indices contains a facility index outside [0, |I|).");
            }

            const double p_ij = pval_buf(k);
            const double y_i = y_buf(i);
            const double q_ij = 1.0 - (1.0 - p_ij) * y_i;

            if (q_ij < min_val) {
                min_val = q_ij;
                argmin_i = i;
                p_argmin = p_ij;
            }

            // At a MIPSOL callback y is integer up to tolerance. For a
            // degenerate customer, the min-based representative must be a
            // selected covering facility.
            if (y_i > 0.5 && q_ij < selected_min_val) {
                selected_min_val = q_ij;
                selected_argmin_i = i;
                selected_p_argmin = p_ij;
            }

            sum_val += p_ij * y_i;
        }

        const double d_j = d_buf(j);

        if (min_val < sum_val - tol) {
            // Strictly min-based customer: j in J_Q.
            base_const += d_j;
            base_coef[static_cast<size_t>(argmin_i)] +=
                -d_j * (1.0 - p_argmin);
            base_lhs_val += d_j * min_val;
        } else {
            // Strictly sum-based or degenerate customer: j in J_N.
            for (int k = start; k < end; ++k) {
                const int i = indices_buf(k);
                base_coef[static_cast<size_t>(i)] += d_j * pval_buf(k);
            }
            base_lhs_val += d_j * sum_val;

            // Eligible dual degeneracy: Q_j = N_j and an active argmin can
            // be identified. If numerical noise prevents this, j stays in
            // the sum-based part of both cuts, which remains valid.
            if (std::abs(min_val - sum_val) <= tol &&
                selected_argmin_i >= 0 &&
                std::abs(selected_min_val - min_val) <= tol) {
                degenerate.push_back({
                    start,
                    end,
                    selected_argmin_i,
                    selected_p_argmin,
                    d_j
                });
            }
        }
    }

    const bool violated = base_lhs_val < theta - tol;

    std::vector<int> base_idx;
    std::vector<double> base_coef_out;
    base_idx.reserve(static_cast<size_t>(nI));
    base_coef_out.reserve(static_cast<size_t>(nI));

    for (int i = 0; i < nI; ++i) {
        const double c = base_coef[static_cast<size_t>(i)];
        if (std::abs(c) > 0.0) {
            base_idx.push_back(i);
            base_coef_out.push_back(c);
        }
    }

    py::dict out;
    out["violated"] = violated;
    out["lhs_val"] = base_lhs_val;
    out["const"] = base_const;
    out["idx"] = base_idx;
    out["coef"] = base_coef_out;
    out["n_degenerate"] = static_cast<int>(degenerate.size());

    // Engineering trick 1: avoid constructing the alternative cut unless
    // the base cut is actually separated and D(y) is nonempty.
    if (!violated || degenerate.empty()) {
        out["has_alt"] = false;
        out["alt_violated"] = false;
        out["alt_lhs_val"] = base_lhs_val;
        out["delta_const"] = 0.0;
        out["delta_idx"] = std::vector<int>{};
        out["delta_coef"] = std::vector<double>{};
        return out;
    }

    double delta_const = 0.0;
    std::vector<double> delta_coef(static_cast<size_t>(nI), 0.0);

    for (const DegenerateRecord& rec : degenerate) {
        // Add the alternative min-based term:
        // d_j * [1 - (1 - p_argmin) y_argmin].
        delta_const += rec.d_j;
        delta_coef[static_cast<size_t>(rec.argmin_i)] +=
            -rec.d_j * (1.0 - rec.p_argmin);

        // Remove the base sum-based term:
        // d_j * sum_i p_ij y_i.
        for (int k = rec.start; k < rec.end; ++k) {
            const int i = indices_buf(k);
            delta_coef[static_cast<size_t>(i)] -= rec.d_j * pval_buf(k);
        }
    }

    std::vector<int> delta_idx;
    std::vector<double> delta_coef_out;
    delta_idx.reserve(static_cast<size_t>(nI));
    delta_coef_out.reserve(static_cast<size_t>(nI));

    double delta_norm = std::abs(delta_const);
    double delta_val = delta_const;

    for (int i = 0; i < nI; ++i) {
        const double c = delta_coef[static_cast<size_t>(i)];
        delta_val += c * y_buf(i);
        if (std::abs(c) > duplicate_tol) {
            delta_idx.push_back(i);
            delta_coef_out.push_back(c);
            delta_norm += std::abs(c);
        }
    }

    // Engineering trick 2: skip an algebraically indistinguishable cut.
    // With positive d_j and a nonempty degenerate set this will rarely fire,
    // but the check is inexpensive and prevents numerical duplicates.
    const bool is_duplicate = delta_norm <= duplicate_tol;
    const double alt_lhs_val = base_lhs_val + delta_val;
    const bool alt_violated = alt_lhs_val < theta - tol;
    const bool has_alt = !is_duplicate && alt_violated;

    out["has_alt"] = has_alt;
    out["alt_violated"] = alt_violated;
    out["alt_lhs_val"] = alt_lhs_val;
    out["delta_const"] = delta_const;
    out["delta_idx"] = delta_idx;
    out["delta_coef"] = delta_coef_out;
    return out;
}

// ============================================================
// Python module
// ============================================================
PYBIND11_MODULE(fast_sep, m) {
    m.doc() = "Fast separation routines for CBC and dual-degeneracy cuts";

    m.def(
        "separate_cbc",
        &separate_cbc,
        py::arg("y"),
        py::arg("theta"),
        py::arg("indptr"),
        py::arg("indices"),
        py::arg("pval"),
        py::arg("d"),
        py::arg("tol") = 1e-6
    );

    m.def(
        "separate_cbc_dual_degeneracy",
        &separate_cbc_dual_degeneracy,
        py::arg("y"),
        py::arg("theta"),
        py::arg("indptr"),
        py::arg("indices"),
        py::arg("pval"),
        py::arg("d"),
        py::arg("tol") = 1e-6,
        py::arg("duplicate_tol") = 1e-8
    );
}
