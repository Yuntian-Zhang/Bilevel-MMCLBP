from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "fast_sep",
        ["fast_sep.cpp"],
        cxx_std=17,
        extra_compile_args=["-O3"],
    ),
]

setup(
    name="fast_sep",
    version="0.1.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
